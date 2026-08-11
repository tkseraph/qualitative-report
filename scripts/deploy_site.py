#!/usr/bin/env python3
"""Build, publish, and roll back the curated static site over SSH."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shlex
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from urllib.error import URLError
from urllib.request import Request, urlopen

try:
    from .site_builder import build_site, load_site_config
except ImportError:  # pragma: no cover - direct script execution
    from site_builder import build_site, load_site_config


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REMOTE_ROOT = "/var/www/value-emergence"
SITE_TESTS = (
    "tests/test_site_builder.py",
    "tests/test_site_security.py",
    "tests/test_publish_report.py",
    "tests/test_deploy_site.py",
)
SAFE_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")
SAFE_HOST = re.compile(r"[A-Za-z0-9][A-Za-z0-9.-]*")
SAFE_USER = re.compile(r"[a-z_][a-z0-9_-]*")


class DeployError(RuntimeError):
    """Raised when a release cannot be published or rolled back safely."""


def _run(
    command: list[str],
    *,
    cwd: Path = PROJECT_ROOT,
    capture_output: bool = False,
) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            command,
            cwd=cwd,
            check=True,
            text=True,
            capture_output=capture_output,
        )
    except FileNotFoundError as exc:
        raise DeployError(f"Required command is unavailable: {command[0]}") from exc
    except subprocess.CalledProcessError as exc:
        raise DeployError(f"Command failed: {command[0]}") from exc


def _validate_connection(args: argparse.Namespace) -> None:
    identity = Path(args.identity).expanduser()
    if not identity.is_file():
        raise DeployError(f"SSH identity does not exist: {identity}")
    if identity.stat().st_mode & 0o077:
        raise DeployError("SSH identity permissions are too broad; use chmod 600")
    if not SAFE_HOST.fullmatch(args.host):
        raise DeployError("Host must be a DNS name or IPv4 address")
    if not SAFE_USER.fullmatch(args.user):
        raise DeployError("Remote user contains unsupported characters")
    if not 1 <= args.port <= 65535:
        raise DeployError("SSH port must be between 1 and 65535")
    _validate_remote_root(args.remote_root)


def _validate_remote_root(value: str) -> str:
    path = PurePosixPath(value)
    if (
        not path.is_absolute()
        or path == PurePosixPath("/")
        or ".." in path.parts
        or any(char.isspace() for char in value)
    ):
        raise DeployError("Remote root must be an absolute path without spaces or parent traversal")
    return path.as_posix().rstrip("/")


def _validate_release_name(value: str) -> str:
    if not SAFE_NAME.fullmatch(value):
        raise DeployError("Release name contains unsupported characters")
    return value


def _ssh_prefix(args: argparse.Namespace) -> list[str]:
    return [
        "ssh",
        "-i",
        str(Path(args.identity).expanduser()),
        "-o",
        "IdentitiesOnly=yes",
        "-o",
        "BatchMode=yes",
        "-o",
        "ConnectTimeout=10",
        "-p",
        str(args.port),
        f"{args.user}@{args.host}",
    ]


def _scp_prefix(args: argparse.Namespace) -> list[str]:
    return [
        "scp",
        "-i",
        str(Path(args.identity).expanduser()),
        "-o",
        "IdentitiesOnly=yes",
        "-o",
        "BatchMode=yes",
        "-P",
        str(args.port),
    ]


def _ssh(args: argparse.Namespace, script: str, *, capture_output: bool = False) -> subprocess.CompletedProcess[str]:
    return _run(_ssh_prefix(args) + [script], capture_output=capture_output)


def _build_digest(output: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(item for item in output.rglob("*") if item.is_file()):
        digest.update(path.relative_to(output).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()[:8]


def _new_release_name(build_digest: str) -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{timestamp}-{build_digest}"


def _validate_build(output: Path) -> int:
    for name in ("index.html", "reports.json", "robots.txt"):
        if not (output / name).is_file():
            raise DeployError(f"Build is missing required file: {name}")
    try:
        reports = json.loads((output / "reports.json").read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        raise DeployError("Build report manifest is invalid") from exc
    for report in reports:
        path = output / str(report.get("public_path", ""))
        if not path.is_file():
            raise DeployError(f"Build is missing report page: {path.relative_to(output)}")
    return sum(1 for path in output.rglob("*") if path.is_file())


def _prepare_build(*, run_tests: bool) -> tuple[Path, int, str]:
    if run_tests:
        _run([sys.executable, "-m", "pytest", "-q", *SITE_TESTS])
    output = build_site(PROJECT_ROOT)
    return output, _validate_build(output), _build_digest(output)


def _current_release(args: argparse.Namespace) -> str:
    root = shlex.quote(_validate_remote_root(args.remote_root))
    result = _ssh(
        args,
        f'target=$(readlink -f {root}/current 2>/dev/null || true); '
        'if [ -n "$target" ]; then basename "$target"; fi',
        capture_output=True,
    )
    value = result.stdout.strip()
    return _validate_release_name(value) if value else ""


def _switch_release(args: argparse.Namespace, release: str, *, expected_files: int | None = None) -> None:
    release = _validate_release_name(release)
    root = _validate_remote_root(args.remote_root)
    release_dir = f"{root}/releases/{release}"
    release_dir_q = shlex.quote(release_dir)
    checks = [
        (
            f"if [ -O {release_dir_q} ]; then "
            f"find {release_dir_q} -type d -exec chmod 0755 {{}} +; "
            f"find {release_dir_q} -type f -exec chmod 0644 {{}} +; fi"
        ),
        f"test ! -e {shlex.quote(release_dir + '/.failed-health-check')}",
        f"test ! -e {shlex.quote(release_dir + '/.uploading')}",
        f"test -f {shlex.quote(release_dir + '/index.html')}",
        f"test -f {shlex.quote(release_dir + '/reports.json')}",
    ]
    if expected_files is not None:
        checks[2] = f"test -e {shlex.quote(release_dir + '/.uploading')}"
        checks.append(
            f'test "$(find {release_dir_q} -type f ! -name .uploading | wc -l)" -eq {expected_files}'
        )
        checks.append(f"unlink {shlex.quote(release_dir + '/.uploading')}")
    temp_link = f"{root}/.current-{release}"
    checks.extend(
        (
            f"ln -sfn {shlex.quote(release_dir)} {shlex.quote(temp_link)}",
            f"mv -Tf {shlex.quote(temp_link)} {shlex.quote(root + '/current')}",
        )
    )
    _ssh(args, "set -eu; " + "; ".join(checks))


def _health_check(
    url: str,
    *,
    attempts: int = 5,
    expected_markers: tuple[str, ...] = ("价值涌现",),
) -> None:
    error = "unknown response"
    for attempt in range(attempts):
        try:
            request = Request(url, headers={"User-Agent": "value-emergence-deployer/1"})
            with urlopen(request, timeout=10) as response:
                body = response.read().decode("utf-8", errors="replace")
                if response.status == 200 and all(marker in body for marker in expected_markers):
                    return
                error = f"unexpected HTTP {response.status} or page marker"
        except (OSError, URLError) as exc:
            error = str(exc)
        if attempt + 1 < attempts:
            time.sleep(1)
    raise DeployError(f"Health check failed: {error}")


def deploy(args: argparse.Namespace) -> str:
    _validate_connection(args)
    previous = _current_release(args)
    output, file_count, build_digest = _prepare_build(run_tests=not args.skip_tests)
    release = _new_release_name(build_digest)
    root = _validate_remote_root(args.remote_root)
    release_dir = f"{root}/releases/{release}"
    _ssh(
        args,
        f"set -eu; test ! -e {shlex.quote(release_dir)}; mkdir -p {shlex.quote(release_dir)}; "
        f"touch {shlex.quote(release_dir + '/.uploading')}",
    )
    destination = f"{args.user}@{args.host}:{release_dir}/"
    _run(_scp_prefix(args) + ["-r", f"{output}/.", destination])
    _switch_release(args, release, expected_files=file_count)
    health_url = args.health_url or f"http://{args.host}/"
    try:
        config = load_site_config(PROJECT_ROOT / "site")
        expected_markers = tuple(
            value
            for value in (
                config.get("site_name", ""),
                config.get("registered_site_name", ""),
                config.get("icp_number", ""),
            )
            if value
        )
        _health_check(health_url, expected_markers=expected_markers)
    except DeployError:
        if previous and previous != release:
            _switch_release(args, previous)
        _ssh(args, f"touch {shlex.quote(release_dir + '/.failed-health-check')}")
        raise
    print(f"Published release: {release}")
    return release


def rollback(args: argparse.Namespace) -> None:
    _validate_connection(args)
    release = _validate_release_name(args.release)
    previous = _current_release(args)
    _switch_release(args, release)
    health_url = args.health_url or f"http://{args.host}/"
    try:
        _health_check(health_url)
    except DeployError:
        if previous and previous != release:
            _switch_release(args, previous)
        raise
    print(f"Rolled back to release: {release}")


def list_releases(args: argparse.Namespace) -> None:
    _validate_connection(args)
    root = _validate_remote_root(args.remote_root)
    root_q = shlex.quote(root)
    script = (
        "set -eu; target=$(readlink -f " + root_q + "/current 2>/dev/null || true); "
        "current=${target##*/}; "
        "for directory in " + root_q + "/releases/*; do "
        "[ -d \"$directory\" ] || continue; name=$(basename \"$directory\"); "
        "if [ -e \"$directory/.uploading\" ]; then printf '? %s (incomplete upload)\\n' \"$name\"; "
        "elif [ -e \"$directory/.failed-health-check\" ]; then printf '! %s (failed health check)\\n' \"$name\"; "
        "elif [ \"$name\" = \"$current\" ]; then printf '* %s\\n' \"$name\"; "
        "else printf '  %s\\n' \"$name\"; fi; done"
    )
    result = _ssh(args, script, capture_output=True)
    print(result.stdout, end="")


def _add_connection_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--host", required=True, help="ECS public IP or DNS name")
    parser.add_argument("--identity", required=True, help="SSH private-key path")
    parser.add_argument("--user", default="value-deploy", help="Remote deployment user")
    parser.add_argument("--port", type=int, default=22, help="SSH port")
    parser.add_argument("--remote-root", default=DEFAULT_REMOTE_ROOT, help="Remote site root")
    parser.add_argument("--health-url", default="", help="URL used after switching releases")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Publish and roll back the curated report website")
    commands = parser.add_subparsers(dest="command", required=True)

    deploy_parser = commands.add_parser("deploy", help="test, build, and publish a new release")
    _add_connection_arguments(deploy_parser)
    deploy_parser.add_argument("--skip-tests", action="store_true", help="skip focused tests")

    list_parser = commands.add_parser("releases", help="list releases and mark the active one")
    _add_connection_arguments(list_parser)

    rollback_parser = commands.add_parser("rollback", help="switch to an existing release")
    rollback_parser.add_argument("release", help="release name from the releases command")
    _add_connection_arguments(rollback_parser)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "deploy":
            deploy(args)
        elif args.command == "releases":
            list_releases(args)
        else:
            rollback(args)
    except DeployError as exc:
        print(f"Deployment failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
