import json
from pathlib import Path

import pytest

from deploy_site import DeployError, _build_digest, _validate_build, _validate_release_name, _validate_remote_root


def _write_minimal_build(root: Path) -> None:
    report_path = Path("reports/000001-sz/qualitative/2026-08-03/index.html")
    (root / report_path).parent.mkdir(parents=True)
    (root / report_path).write_text("report", encoding="utf-8")
    (root / "index.html").write_text("catalog", encoding="utf-8")
    (root / "robots.txt").write_text("User-agent: *\nDisallow: /\n", encoding="utf-8")
    (root / "reports.json").write_text(
        json.dumps([{"public_path": report_path.as_posix()}]),
        encoding="utf-8",
    )


def test_validate_build_requires_every_manifest_report(tmp_path):
    _write_minimal_build(tmp_path)

    assert _validate_build(tmp_path) == 4

    next(iter((tmp_path / "reports").rglob("index.html"))).unlink()
    with pytest.raises(DeployError, match="missing report page"):
        _validate_build(tmp_path)


def test_build_digest_changes_with_public_content(tmp_path):
    _write_minimal_build(tmp_path)
    first = _build_digest(tmp_path)

    (tmp_path / "index.html").write_text("updated catalog", encoding="utf-8")

    assert _build_digest(tmp_path) != first


@pytest.mark.parametrize("value", ["release;touch-x", "../release", "release name", ""])
def test_validate_release_name_rejects_shell_metacharacters(value):
    with pytest.raises(DeployError):
        _validate_release_name(value)


def test_validate_remote_root_requires_safe_absolute_path():
    assert _validate_remote_root("/var/www/value-emergence/") == "/var/www/value-emergence"
    with pytest.raises(DeployError):
        _validate_remote_root("../../tmp/site")
    with pytest.raises(DeployError):
        _validate_remote_root("/var/www/site name")
    with pytest.raises(DeployError):
        _validate_remote_root("/")
