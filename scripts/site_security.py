#!/usr/bin/env python3
"""Safety checks for files entering the public report website."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Iterable


SECRET_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "OpenAI-style API key",
        re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}\b", re.IGNORECASE),
    ),
    (
        "GitHub token",
        re.compile(r"\b(?:github_pat_[A-Za-z0-9_]{20,}|gh[pousr]_[A-Za-z0-9]{20,})\b"),
    ),
    ("AWS access key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("Google API key", re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b")),
    (
        "Slack token",
        re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b", re.IGNORECASE),
    ),
    (
        "private key block",
        re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----"),
    ),
    (
        "credential assignment",
        re.compile(
            r"(?:api[_-]?key|api[_-]?token|access[_-]?token|auth[_-]?token|"
            r"secret[_-]?key|client[_-]?secret|password|tushare[_-]?token)"
            r"\s*[:=]\s*[\"']?"
            r"(?!(?:your|replace|changeme|example|dummy|test|xxx|<|\$\{|\{\{))"
            r"[A-Za-z0-9_./+=-]{16,}",
            re.IGNORECASE,
        ),
    ),
    (
        "URL-embedded credential",
        re.compile(
            r"(?:https?|postgres(?:ql)?|mysql|mongodb(?:\+srv)?|redis)://"
            r"[^\s/:@]+:[^\s@]+@",
            re.IGNORECASE,
        ),
    ),
)

LOCAL_PATH_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("macOS user path", re.compile(r"/Users/[^/\s<>'\"]+")),
    ("Windows user path", re.compile(r"[A-Za-z]:\\Users\\[^\\\s<>'\"]+")),
    ("local file URL", re.compile(r"\bfile://", re.IGNORECASE)),
)

TEXT_SUFFIXES = {".html", ".htm", ".css", ".js", ".json", ".xml", ".txt"}


def _clean_env_value(raw: str) -> str:
    value = raw.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        value = value[1:-1]
    return value.strip()


def _looks_like_real_secret(value: str) -> bool:
    if len(value) < 12:
        return False
    lowered = value.lower()
    placeholders = ("your_", "replace", "changeme", "example", "dummy", "test", "xxx", "${", "{{", "<")
    return not lowered.startswith(placeholders)


def _walk_strings(value: object) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from _walk_strings(item)
    elif isinstance(value, dict):
        for item in value.values():
            yield from _walk_strings(item)


def load_known_local_secrets(project_root: Path) -> tuple[str, ...]:
    """Load local secret values without exposing their names or contents."""
    secrets: set[str] = set()
    env_path = project_root / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8", errors="ignore").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            name, raw = stripped.split("=", 1)
            if not re.search(r"(?:key|token|secret|password)", name, re.IGNORECASE):
                continue
            value = _clean_env_value(raw)
            if _looks_like_real_secret(value):
                secrets.add(value)

    settings_path = project_root / ".claude" / "settings.json"
    if settings_path.exists():
        try:
            settings = json.loads(settings_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            settings = {}
        assignment = re.compile(
            r"(?:api[_-]?key|api[_-]?token|access[_-]?token|auth[_-]?token|"
            r"secret[_-]?key|client[_-]?secret|password|tushare[_-]?token)"
            r"\s*=\s*['\"]?([^'\"\s)]+)",
            re.IGNORECASE,
        )
        for text in _walk_strings(settings):
            for match in assignment.finditer(text):
                value = match.group(1)
                if _looks_like_real_secret(value):
                    secrets.add(value)

    return tuple(sorted(secrets, key=len, reverse=True))


def inspect_public_text(
    text: str,
    *,
    known_secrets: Iterable[str] = (),
    require_report_contract: bool = False,
) -> list[str]:
    """Return sanitized findings; never return the matched secret value."""
    findings: list[str] = []
    for value in known_secrets:
        if value and value in text:
            findings.append("known local secret value")
            break

    for label, pattern in SECRET_PATTERNS:
        if pattern.search(text):
            findings.append(label)

    for label, pattern in LOCAL_PATH_PATTERNS:
        if pattern.search(text):
            findings.append(label)

    if "terancejiang.com" in text.lower():
        findings.append("upstream site URL")

    if require_report_contract:
        lowered = text.lower()
        if "<!doctype html" not in lowered or "<title>" not in lowered:
            findings.append("invalid HTML report shell")
        if "不构成投资建议" not in text:
            findings.append("missing investment disclaimer")

    return sorted(set(findings))


def inspect_public_tree(public_root: Path, *, known_secrets: Iterable[str] = ()) -> dict[str, list[str]]:
    findings: dict[str, list[str]] = {}
    if not public_root.exists():
        return findings
    for path in sorted(public_root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        issues = inspect_public_text(
            path.read_text(encoding="utf-8", errors="ignore"),
            known_secrets=known_secrets,
        )
        if issues:
            findings[path.relative_to(public_root).as_posix()] = issues
    return findings
