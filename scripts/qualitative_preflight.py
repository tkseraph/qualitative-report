#!/usr/bin/env python3
"""Production input barrier for qualitative report generation."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import date
from pathlib import Path


REQUIRED_SECTIONS = ("P2", "P3", "P4", "P6", "P13", "MDA", "SUB")
REQUIRED_REPORT_NOTES = ("P2", "P3", "P4", "P6", "P13", "SUB")
REQUIRED_FILES = (
    "annual_report.pdf",
    "data_pack_market.md",
    "computed_metrics.md",
    "pdf_sections.json",
    "data_pack_report.md",
    "peer_evidence.md",
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _issue(code: str, message: str, *, blocking: bool = True) -> dict:
    return {"code": code, "message": message, "blocking": blocking}


def audit_inputs(output_dir: Path) -> dict:
    issues: list[dict] = []
    files: dict[str, dict] = {}
    for name in REQUIRED_FILES:
        path = output_dir / name
        if not path.is_file() or path.stat().st_size == 0:
            issues.append(_issue("missing_input", f"missing or empty: {name}"))
            continue
        files[name] = {
            "size": path.stat().st_size,
            "sha256": _sha256(path),
        }

    pdf_path = output_dir / "annual_report.pdf"
    if pdf_path.is_file() and pdf_path.read_bytes()[:5] != b"%PDF-":
        issues.append(_issue("invalid_pdf_header", "annual_report.pdf lacks a PDF header"))

    sections_path = output_dir / "pdf_sections.json"
    if sections_path.is_file():
        try:
            sections = json.loads(sections_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            issues.append(_issue("invalid_pdf_sections", str(exc)))
            sections = {}
        for section in REQUIRED_SECTIONS:
            value = sections.get(section)
            if not isinstance(value, str) or len(value.strip()) < 40:
                issues.append(_issue("missing_pdf_section", f"{section} has no usable extraction"))
            elif not re.search(r"--- p\.\d+ ---", value):
                issues.append(_issue("missing_pdf_locator", f"{section} lacks physical-page locator"))
        diagnostics = sections.get("metadata", {}).get("section_diagnostics", {})
        if diagnostics:
            for section in REQUIRED_SECTIONS:
                confidence = diagnostics.get(section, {}).get("confidence")
                if confidence in {"low", "missing", None}:
                    issues.append(_issue("low_section_confidence", f"{section} confidence={confidence}"))
        else:
            issues.append(_issue(
                "legacy_pdf_sections",
                "section diagnostics absent; audited note pack must provide the manual-review barrier",
                blocking=False,
            ))

    notes_path = output_dir / "data_pack_report.md"
    if notes_path.is_file():
        notes = notes_path.read_text(encoding="utf-8", errors="ignore")
        if "年报原页复核" not in notes and "原页复核" not in notes:
            issues.append(_issue(
                "unaudited_note_pack",
                "data_pack_report.md must declare annual-report source-page review",
            ))
        for section in REQUIRED_REPORT_NOTES:
            if not re.search(rf"^##\s+{re.escape(section)}\.", notes, flags=re.MULTILINE):
                issues.append(_issue("missing_note_section", f"data_pack_report.md lacks {section}"))
        if len(re.findall(r"(?:PDF\s*)?p\.\d+", notes, flags=re.IGNORECASE)) < 6:
            issues.append(_issue("insufficient_note_locators", "note pack needs page locators for every section"))

    peer_path = output_dir / "peer_evidence.md"
    if peer_path.is_file():
        peer = peer_path.read_text(encoding="utf-8", errors="ignore")
        high_count = len(re.findall(r"\bHigh\b", peer))
        first_cells = re.findall(r"^\|\s*([^|\n]+?)\s*\|", peer, flags=re.MULTILINE)
        peer_names = {
            cell.strip()
            for cell in first_cells
            if any(suffix in cell for suffix in ("集团", "股份", "控股", "乳业", "食品", "科技", "实业"))
            and cell.strip() not in {"Peer", "Company", "公司", "同业"}
        }
        if high_count < 4:
            issues.append(_issue("weak_peer_evidence", "peer_evidence.md needs at least four High evidence rows"))
        if len(peer_names) < 2:
            issues.append(_issue("insufficient_named_peers", "peer evidence needs at least two named comparable companies"))
        if "Evidence Gaps" not in peer and "证据缺口" not in peer:
            issues.append(_issue("missing_peer_gaps", "peer evidence must disclose comparability gaps"))

    blocking = [issue for issue in issues if issue["blocking"]]
    return {
        "schema_version": "1.0",
        "generated_on": date.today().isoformat(),
        "output_dir": output_dir.name,
        "status": "pass" if not blocking else "fail",
        "files": files,
        "issues": issues,
    }


def write_manifest(output_dir: Path, audit: dict) -> Path:
    path = output_dir / "qualitative_input_manifest.json"
    path.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate production inputs for a qualitative report")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--no-write", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    output_dir = Path(args.output_dir).expanduser().resolve()
    if not output_dir.is_dir():
        print(f"Output directory not found: {output_dir}")
        return 2
    audit = audit_inputs(output_dir)
    if not args.no_write:
        print(f"Input manifest: {write_manifest(output_dir, audit)}")
    for issue in audit["issues"]:
        level = "ERROR" if issue["blocking"] else "WARN"
        print(f"[{level}] {issue['code']}: {issue['message']}")
    print(f"Production preflight: {audit['status'].upper()}")
    return 0 if audit["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
