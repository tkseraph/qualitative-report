#!/usr/bin/env python3
"""Create WeChat Official Account drafts from finished Markdown reports."""

from __future__ import annotations

import argparse
import re
import shlex
import subprocess
from pathlib import Path

from validate_reports import validate_file
from report_to_html import render_report_html

REPORT_TYPES = ("qualitative", "turtle", "valuation")
CREDENTIAL_LIKE_ARGS = {"--appid", "--appsecret", "--secret", "--token"}


def discover_report(path: Path, report_type: str | None, explicit_file: Path | None) -> Path:
    if explicit_file is not None:
        if not explicit_file.exists():
            raise SystemExit(f"Report file not found: {explicit_file}")
        return explicit_file
    if path.is_file():
        if path.suffix.lower() != ".md":
            raise SystemExit(f"Expected a Markdown report file: {path}")
        return path
    if not path.exists():
        raise SystemExit(f"Path not found: {path}")
    if report_type is None:
        raise SystemExit("--type is required when path is an output directory")
    matches = sorted(path.glob(f"*_{report_type}_report.md"))
    if not matches:
        raise SystemExit(f"Missing {report_type} report in: {path}")
    if len(matches) > 1:
        raise SystemExit(
            f"Multiple {report_type} reports found; keep exactly one: "
            + ", ".join(str(match) for match in matches)
        )
    return matches[0]


def infer_report_type(report_path: Path) -> str:
    for report_type in REPORT_TYPES:
        if report_path.name.endswith(f"_{report_type}_report.md"):
            return report_type
    known = ", ".join(f"*_{report_type}_report.md" for report_type in REPORT_TYPES)
    raise SystemExit(f"Cannot infer report type from filename: {report_path.name}. Expected: {known}")


def validate_before_draft(report_path: Path, report_type: str) -> None:
    result = validate_file(report_path, report_type)
    if not result.ok:
        messages = "\n".join(f"- {message}" for message in result.messages)
        raise SystemExit(f"Report validation failed: {report_path}\n{messages}")


def _section_body(md_text: str, title_keywords: tuple[str, ...]) -> str:
    sections = re.split(r"(?=^## )", md_text, flags=re.MULTILINE)
    for section in sections:
        header_match = re.match(r"##\s+(.+?)(?:\n|$)", section)
        if not header_match:
            continue
        title = header_match.group(1)
        if any(keyword in title for keyword in title_keywords):
            return section[header_match.end():].strip()
    return ""


def _first_sentence(text: str) -> str:
    compact = re.sub(r"\s+", " ", text).strip()
    compact = re.sub(r"^[-*>#\s]+", "", compact)
    match = re.search(r"^(.+?[。！？.!?])", compact)
    return match.group(1).strip() if match else compact


def _trim_digest(text: str, max_chars: int = 110) -> str:
    compact = re.sub(r"\s+", " ", text).strip()
    if len(compact) <= max_chars:
        return compact
    return compact[: max_chars - 1].rstrip("，,。；;、 ") + "…"


def auto_digest_from_qualitative(md_text: str) -> str:
    summary = _section_body(md_text, ("Executive Summary", "执行摘要"))
    if summary:
        first = _first_sentence(summary)
        if first:
            return _trim_digest(first)

    verdict = _section_body(md_text, ("Business Quality Verdict", "商业质量总体评级"))
    if verdict:
        first = _first_sentence(verdict)
        if first:
            return _trim_digest(first)

    title_match = re.search(r"^#\s+(.+?)(?:—|-|$)", md_text, flags=re.MULTILINE)
    if title_match:
        return _trim_digest(f"{title_match.group(1).strip()}商业质量定性分析")
    return "商业质量定性分析"


def _clean_card_value(value: str) -> str:
    return re.sub(r"[*`]+", "", value).strip()


def _extract_card_value(md_text: str, keywords: tuple[str, ...], fallback: str = "见正文") -> str:
    for keyword in keywords:
        pattern = rf"(?:{re.escape(keyword)})[：:]\s*(.+)$"
        match = re.search(pattern, md_text, flags=re.MULTILINE)
        if not match:
            continue
        raw_value = match.group(1).strip()
        emphasized = re.match(r"^(\*\*|\*)(.+?)\1", raw_value)
        value = emphasized.group(2) if emphasized else _first_sentence(raw_value)
        value = _clean_card_value(value)
        if value:
            return _trim_digest(value, 80)
    return fallback


def _first_screen_card(md_text: str) -> str:
    company_essence = _extract_card_value(md_text, ("公司本质",), _trim_digest(auto_digest_from_qualitative(md_text), 80))
    quality = _extract_card_value(md_text, ("商业质量", "综合判断", "总体评级"), "见 Business Quality Verdict")
    moat = _extract_card_value(md_text, ("护城河来源", "核心优势", "优势来自"), "见维度二")
    risk = _extract_card_value(md_text, ("最大风险", "核心风险", "主要风险", "主要约束"), "见核心矛盾")
    cycle = _extract_card_value(md_text, ("周期位置", "当前周期"), "不适用 / 见外部环境")
    refutation = _extract_card_value(md_text, ("反证条件", "重评触发", "重评动作"), "见核心矛盾与未来观察变量")
    return "\n".join([
        "| 项目 | 结论 |",
        "|---|---|",
        f"| 公司本质 | {company_essence} |",
        f"| 商业质量 | {quality} |",
        f"| 护城河来源 | {moat} |",
        f"| 最大风险 | {risk} |",
        f"| 周期位置 | {cycle} |",
        f"| 反证条件 | {refutation} |",
    ])


def _has_first_screen_card(md_text: str) -> bool:
    return all(marker in md_text for marker in (
        "| 项目 | 结论 |",
        "| 公司本质 |",
        "| 商业质量 |",
        "| 护城河来源 |",
        "| 最大风险 |",
    ))


def polish_qualitative_markdown(md_text: str) -> str:
    polished = md_text
    if not _has_first_screen_card(polished):
        verdict_header = re.search(
            r"(^##\s+.*?(?:Business Quality Verdict|商业质量总体评级).*?\n)",
            polished,
            flags=re.MULTILINE,
        )
        if verdict_header:
            insert_at = verdict_header.end()
            polished = polished[:insert_at] + "\n" + _first_screen_card(polished) + "\n\n" + polished[insert_at:]
    polished = re.sub(
        r"^##\s+结构化参数\s*$",
        "## 结构化参数（机器读取 / 附录）",
        polished,
        flags=re.MULTILINE,
    )
    return polished


def create_polished_qualitative_markdown(report_path: Path, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    polished_path = output_dir / f"{report_path.stem}.polished.md"
    polished_path.write_text(
        polish_qualitative_markdown(report_path.read_text(encoding="utf-8")),
        encoding="utf-8",
    )
    return polished_path


def preview_html_path_for(report_path: Path, output_dir: Path) -> Path:
    stem = report_path.stem
    if stem.endswith(".polished"):
        stem = stem.removesuffix(".polished")
    return output_dir / f"{stem}.preview.html"


def build_wxgzh_command(
    report_path: Path,
    *,
    output_dir: Path,
    account: str | None,
    author: str | None,
    digest: str | None,
    theme: str | None,
    cover: Path | None,
    no_cover: bool,
) -> list[str]:
    command = ["npx", "-y", "@lyhue1991/wxgzh", str(report_path), "--output-dir", str(output_dir)]
    if account:
        command.extend(["--account", account])
    if author:
        command.extend(["--author", author])
    if digest:
        command.extend(["--digest", digest])
    if theme:
        command.extend(["--theme", theme])
    if cover is not None:
        command.extend(["--cover", str(cover)])
    if no_cover:
        command.append("--no-cover")
    return command


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create draft-box entries from finished Turtle Investment Framework reports"
    )
    parser.add_argument("path", type=Path, help="Output directory or Markdown report file")
    parser.add_argument("--type", choices=REPORT_TYPES, help="Report type when path is an output directory")
    parser.add_argument("--file", type=Path, help="Explicit Markdown report file")
    parser.add_argument("--account", help="wxgzh account name")
    parser.add_argument("--author", help="Article author passed to wxgzh")
    parser.add_argument("--digest", help="Article digest passed to wxgzh")
    parser.add_argument("--theme", help="wxgzh theme name")
    parser.add_argument("--cover", type=Path, help="Cover image path passed to wxgzh")
    parser.add_argument("--no-cover", action="store_true", help="Pass --no-cover to wxgzh")
    parser.add_argument("--output-dir", type=Path, help="wxgzh output directory")
    parser.add_argument("--skip-validation", action="store_true", help="Skip finished-report validation")
    parser.add_argument(
        "--qualitative-polish",
        action="store_true",
        help="Create a presentation-polished qualitative Markdown copy under .wxgzh before drafting",
    )
    parser.add_argument(
        "--preview-html",
        action="store_true",
        help="Generate a local standalone HTML preview for qualitative polish mode",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print the npx command without running it")
    parser.add_argument("--yes", action="store_true", help="Required for real draft creation")
    args, unknown = parser.parse_known_args(argv)
    credential_args = [arg for arg in unknown if arg.split("=", 1)[0].lower() in CREDENTIAL_LIKE_ARGS]
    if credential_args:
        raise SystemExit(
            "Credential-like arguments are not supported: "
            + ", ".join(credential_args)
            + ". Configure wxgzh credentials outside this project."
        )
    if unknown:
        parser.error("unrecognized arguments: " + " ".join(unknown))
    return args


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)
    report_path = discover_report(args.path, args.type, args.file)
    inferred_report_type = infer_report_type(report_path) if args.qualitative_polish else None
    if args.qualitative_polish and inferred_report_type != "qualitative":
        raise SystemExit("--qualitative-polish only supports qualitative reports")
    report_type = args.type or inferred_report_type or infer_report_type(report_path)

    if not args.skip_validation:
        validate_before_draft(report_path, report_type)

    output_dir = args.output_dir or report_path.parent / ".wxgzh"
    draft_report_path = report_path
    digest = args.digest
    if args.preview_html and not args.qualitative_polish:
        raise SystemExit("--preview-html requires --qualitative-polish")
    if args.qualitative_polish:
        draft_report_path = create_polished_qualitative_markdown(report_path, output_dir)
        if digest is None:
            digest = auto_digest_from_qualitative(report_path.read_text(encoding="utf-8"))
    if args.preview_html:
        preview_path = preview_html_path_for(draft_report_path, output_dir)
        render_report_html(draft_report_path, preview_path, standalone=True)

    command = build_wxgzh_command(
        draft_report_path,
        output_dir=output_dir,
        account=args.account,
        author=args.author,
        digest=digest,
        theme=args.theme,
        cover=args.cover,
        no_cover=args.no_cover,
    )
    if args.dry_run:
        print(shlex.join(command))
        return
    if not args.yes:
        raise SystemExit("--yes is required for real draft creation")
    subprocess.run(command, check=True)


if __name__ == "__main__":
    main()
