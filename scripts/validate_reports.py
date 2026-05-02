#!/usr/bin/env python3
"""Validate finished report Markdown files against product schemas."""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path

from report_schema import REPORT_SCHEMAS, ReportSchema, SchemaRequirement


@dataclass(frozen=True)
class ValidationResult:
    report_type: str
    path: str
    ok: bool
    missing: list[str]
    messages: list[str]


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).lower()


def _has_any_keyword(normalized_text: str, requirement: SchemaRequirement) -> bool:
    return any(keyword.lower() in normalized_text for keyword in requirement.any_keywords)


def _missing_requirements(md_text: str, schema: ReportSchema) -> list[SchemaRequirement]:
    normalized = _normalize(md_text)
    return [
        requirement
        for requirement in schema.requirements
        if not _has_any_keyword(normalized, requirement)
    ]


def validate_markdown(md_text: str, report_type: str, path: str = "<memory>") -> ValidationResult:
    schema = REPORT_SCHEMAS.get(report_type)
    if schema is None:
        known = ", ".join(sorted(REPORT_SCHEMAS))
        return ValidationResult(
            report_type=report_type,
            path=path,
            ok=False,
            missing=[report_type],
            messages=[f"Unknown report type: {report_type}. Expected one of: {known}"],
        )

    missing_requirements = _missing_requirements(md_text, schema)
    messages = [
        f"Missing {requirement.name}: {requirement.description} "
        f"(expected one of: {', '.join(requirement.any_keywords)})"
        for requirement in missing_requirements
    ]
    return ValidationResult(
        report_type=report_type,
        path=path,
        ok=not missing_requirements,
        missing=[requirement.name for requirement in missing_requirements],
        messages=messages,
    )


def validate_file(path: Path, report_type: str) -> ValidationResult:
    if not path.exists():
        return ValidationResult(
            report_type=report_type,
            path=str(path),
            ok=False,
            missing=["file"],
            messages=[f"Missing file: {path}"],
        )
    return validate_markdown(path.read_text(encoding="utf-8"), report_type, str(path))


def _find_one(output_dir: Path, pattern: str) -> Path | None:
    matches = sorted(output_dir.glob(pattern))
    return matches[0] if matches else None


def validate_output_dir(output_dir: Path) -> list[ValidationResult]:
    report_files = {
        "qualitative": _find_one(output_dir, "*_qualitative_report.md"),
        "turtle": _find_one(output_dir, "*_turtle_report.md"),
        "valuation": _find_one(output_dir, "*_valuation_report.md"),
    }
    results: list[ValidationResult] = []
    for report_type, path in report_files.items():
        if path is None:
            expected = output_dir / f"*_{report_type}_report.md"
            results.append(
                ValidationResult(
                    report_type=report_type,
                    path=str(expected),
                    ok=False,
                    missing=["file"],
                    messages=[f"Missing {report_type} report matching {expected}"],
                )
            )
        else:
            results.append(validate_file(path, report_type))
    return results


def _print_result(result: ValidationResult) -> None:
    status = "PASS" if result.ok else "FAIL"
    print(f"[{status}] {result.report_type}: {result.path}")
    for message in result.messages:
        print(f"  - {message}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate finished A-share report outputs")
    parser.add_argument("path", help="Markdown report file or output directory")
    parser.add_argument(
        "--type",
        choices=sorted(REPORT_SCHEMAS),
        help="Report type when validating a single Markdown file",
    )
    args = parser.parse_args()

    path = Path(args.path)
    if path.is_dir():
        results = validate_output_dir(path)
    else:
        if args.type is None:
            raise SystemExit("--type is required when validating a single Markdown file")
        results = [validate_file(path, args.type)]

    for result in results:
        _print_result(result)

    if not all(result.ok for result in results):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
