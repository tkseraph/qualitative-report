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


def _template_placeholder_messages(md_text: str) -> list[str]:
    messages: list[str] = []
    brace_matches = sorted(
        {
            match.group(0)
            for match in re.finditer(r"\{([^{}\n]{1,40})\}", md_text)
            if not re.search(r"[:,]", match.group(1))
        }
    )
    if brace_matches:
        messages.append(
            "Unreplaced template placeholder(s): " + ", ".join(brace_matches[:5])
        )
    todo_matches = sorted(set(re.findall(r"\b(?:TODO|TBD)\b", md_text, re.IGNORECASE)))
    if todo_matches:
        messages.append(
            "Unreplaced template placeholder(s): " + ", ".join(todo_matches)
        )
    return messages


def _content_quality_issues(md_text: str, report_type: str) -> list[tuple[str, str]]:
    normalized = _normalize(md_text)
    issues: list[tuple[str, str]] = []
    if report_type == "valuation" and re.search(r"(?:原始|raw|结果|为|:|：)\s*DCF[^\n]{0,20}[-－]\s*\d|DCF\s*(?:为|:|：)\s*[-－]\s*\d", md_text, re.IGNORECASE):
        has_diagnostic = "方法适配性诊断" in md_text
        has_demotion = any(term in md_text for term in ("降权", "降级", "权重降至", "权重为 0", "权重为0"))
        has_no_domination = any(term in md_text for term in ("不得机械主导", "不机械主导", "不应主导", "不能机械主导"))
        if not has_diagnostic or not has_demotion or not has_no_domination:
            issues.append((
                "negative_dcf_demotion",
                "Report mentions negative DCF but does not clearly demote it as a method-fit diagnostic that must not mechanically dominate valuation.",
            ))
    if report_type == "turtle" and re.search(r"(?:AA|GG|穿透回报率)\s*(?:为|=|:|：)?\s*(?:负值|[-－]\s*\d)", md_text, re.IGNORECASE):
        has_diagnostic = "诊断值" in md_text
        has_wait = any(term in normalized for term in ("wait", "不建仓", "等待", "观察"))
        verdict_text = "\n".join(
            line for line in md_text.splitlines()
            if any(term in line for term in ("Strategy Verdict", "仓位建议", "行动建议", "一句话结论"))
        )
        verdict_normalized = _normalize(verdict_text)
        has_buy_verdict = any(term in verdict_normalized for term in ("buy", "买入"))
        if not has_diagnostic or has_buy_verdict or not has_wait:
            issues.append((
                "negative_turtle_return",
                "Report mentions negative AA/GG or penetrating return but does not clearly treat it as diagnostic with WAIT / no-position guidance.",
            ))
    return issues


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
    placeholder_messages = _template_placeholder_messages(md_text)
    content_issues = _content_quality_issues(md_text, report_type)
    messages = [
        f"Missing {requirement.name}: {requirement.description} "
        f"(expected one of: {', '.join(requirement.any_keywords)})"
        for requirement in missing_requirements
    ] + placeholder_messages + [message for _, message in content_issues]
    missing = [requirement.name for requirement in missing_requirements]
    if placeholder_messages:
        missing.append("template_placeholder")
    missing.extend(name for name, _ in content_issues)
    return ValidationResult(
        report_type=report_type,
        path=path,
        ok=not missing,
        missing=missing,
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


def _find_matches(output_dir: Path, pattern: str) -> list[Path]:
    return sorted(output_dir.glob(pattern))


def _report_prefix(path: Path, report_type: str) -> str:
    suffix = f"_{report_type}_report.md"
    return path.name.removesuffix(suffix)


def _company_identity(md_text: str) -> str | None:
    first_heading = next(
        (line.strip() for line in md_text.splitlines() if line.strip().startswith("# ")),
        "",
    )
    if not first_heading:
        return None
    heading = first_heading.removeprefix("# ").strip()
    heading = re.sub(r"^(龟龟投资策略|估值分析报告|分析报告)[：:·\s-]*", "", heading).strip()
    if "：" in heading:
        heading = heading.rsplit("：", 1)[1].strip()
    if ":" in heading:
        heading = heading.rsplit(":", 1)[1].strip()
    for separator in ("（", "(", "·", "—", "-"):
        if separator in heading:
            heading = heading.split(separator, 1)[0].strip()
    return heading or None


def _normalize_company_identity(identity: str) -> str:
    normalized = re.sub(r"[\s·—\-（）()：:]", "", identity)
    for suffix in ("集团股份有限公司", "股份有限公司", "集团有限公司", "有限公司", "集团"):
        normalized = normalized.removesuffix(suffix)
    return normalized


def _stock_codes(md_text: str) -> set[str]:
    return {
        f"{match.group(1)}.{match.group(2).upper()}"
        for match in re.finditer(r"\b(\d{6})[._](SH|SZ)\b", md_text, re.IGNORECASE)
    }


def _validate_content_identity(selected_files: dict[str, Path]) -> ValidationResult | None:
    texts = {
        report_type: path.read_text(encoding="utf-8")
        for report_type, path in selected_files.items()
    }
    codes = {report_type: _stock_codes(text) for report_type, text in texts.items()}
    known_codes = [next(iter(values)) for values in codes.values() if len(values) == 1]
    if len(known_codes) == len(selected_files) and len(set(known_codes)) == 1:
        return None

    identities = {
        report_type: _company_identity(text)
        for report_type, text in texts.items()
    }
    known_identities = {identity for identity in identities.values() if identity}
    normalized_identities = {
        _normalize_company_identity(identity)
        for identity in known_identities
        if _normalize_company_identity(identity)
    }
    if len(normalized_identities) <= 1:
        return None
    return ValidationResult(
        report_type="directory",
        path=str(next(iter(selected_files.values())).parent),
        ok=False,
        missing=["identity_mismatch"],
        messages=[
            "Reports must describe the same company identity: "
            + ", ".join(
                f"{key}={value or '<unknown>'}"
                for key, value in sorted(identities.items())
            )
        ],
    )


def validate_output_dir(output_dir: Path) -> list[ValidationResult]:
    report_matches = {
        "qualitative": _find_matches(output_dir, "*_qualitative_report.md"),
        "turtle": _find_matches(output_dir, "*_turtle_report.md"),
        "valuation": _find_matches(output_dir, "*_valuation_report.md"),
    }
    results: list[ValidationResult] = []
    selected_files: dict[str, Path] = {}
    for report_type, matches in report_matches.items():
        if not matches:
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
        elif len(matches) > 1:
            results.append(
                ValidationResult(
                    report_type=report_type,
                    path=str(output_dir),
                    ok=False,
                    missing=["duplicate_files"],
                    messages=[
                        f"Multiple {report_type} reports found; keep exactly one: "
                        + ", ".join(str(path) for path in matches)
                    ],
                )
            )
        else:
            selected_files[report_type] = matches[0]
            results.append(validate_file(matches[0], report_type))

    if len(selected_files) == len(REPORT_SCHEMAS):
        prefixes = {
            report_type: _report_prefix(path, report_type)
            for report_type, path in selected_files.items()
        }
        if len(set(prefixes.values())) > 1:
            results.append(
                ValidationResult(
                    report_type="directory",
                    path=str(output_dir),
                    ok=False,
                    missing=["prefix_mismatch"],
                    messages=[
                        "Reports must share the same code_market prefix: "
                        + ", ".join(f"{key}={value}" for key, value in sorted(prefixes.items()))
                    ],
                )
            )
        identity_result = _validate_content_identity(selected_files)
        if identity_result is not None:
            results.append(identity_result)
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
    if not path.exists():
        raise SystemExit(f"Path not found: {path}")
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
