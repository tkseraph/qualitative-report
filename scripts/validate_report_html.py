#!/usr/bin/env python3
"""Validate rendered qualitative HTML and write its render manifest."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from bs4 import BeautifulSoup

try:
    from qualitative_artifacts import report_structure_signature
    from qualitative_quality import rating_from_markdown, structured_param
    from report_contract import report_contract
except ModuleNotFoundError:
    from scripts.qualitative_artifacts import report_structure_signature
    from scripts.qualitative_quality import rating_from_markdown, structured_param
    from scripts.report_contract import report_contract


def validate_html(html_text: str, markdown_text: str) -> tuple[list[str], dict]:
    contract = report_contract("qualitative")
    soup = BeautifulSoup(html_text, "html.parser")
    errors: list[str] = []
    dimensions = [
        heading for heading in soup.select("h2")
        if re.search(r"维度[一二三四五六]|\bD[1-6]\b", heading.get_text(" ", strip=True))
    ]
    expected_dimensions = contract["html"]["required_dimension_count"]
    if len(dimensions) != expected_dimensions:
        errors.append(f"expected {expected_dimensions} rendered dimensions, got {len(dimensions)}")

    markdown_dimension_headings = [
        re.sub(r"\s+", " ", title).strip()
        for title in re.findall(
            r"^##\s+((?:维度[一二三四五六]|D[1-6]\b).*?)\s*$",
            markdown_text,
            flags=re.MULTILINE | re.IGNORECASE,
        )
    ]
    rendered_dimension_headings: list[str] = []
    for heading in dimensions:
        rendered = re.sub(r"\s+", " ", heading.get_text(" ", strip=True)).strip()
        for badge in heading.select(".tag"):
            badge_text = re.sub(r"\s+", " ", badge.get_text(" ", strip=True)).strip()
            if badge_text and rendered.endswith(badge_text):
                rendered = rendered[: -len(badge_text)].strip()
        rendered_dimension_headings.append(rendered)
    dimension_headings_match = markdown_dimension_headings == rendered_dimension_headings
    if not dimension_headings_match:
        errors.append("rendered dimension headings or order differ from source Markdown")

    visible_text = soup.get_text("\n", strip=True)
    raw_patterns = (
        r"\[src\s*:",
        r"^#{2,6}\s",
        r"\*\*[^*]+\*\*",
        r"chart_ready:\s*true",
        r"\bCM§\d+",
        r"\bDP§[A-Za-z0-9]+",
    )
    raw_markdown_absent = not any(
        re.search(pattern, visible_text, flags=re.MULTILINE | re.IGNORECASE)
        for pattern in raw_patterns
    )
    if not raw_markdown_absent:
        errors.append("visible HTML contains raw Markdown or internal source markers")

    required_open = contract["html"]["default_open_table_roles"]
    open_roles: list[str] = []
    for role in required_open:
        nodes = soup.select(f'details[data-component-role="{role}"]')
        if len(nodes) != 1:
            errors.append(f"expected exactly one {role} component, got {len(nodes)}")
            continue
        if not nodes[0].has_attr("open"):
            errors.append(f"{role} component must be open by default")
        else:
            open_roles.append(role)

    expected_chart_count = len(re.findall(r"^chart_ready:\s*true\s*;", markdown_text, flags=re.MULTILINE))
    chart_nodes = soup.select(".chart-container")
    if len(chart_nodes) != expected_chart_count:
        errors.append(f"expected {expected_chart_count} chart containers, got {len(chart_nodes)}")
    golden_chart_count_ok = True
    if structured_param(markdown_text, "analysis_contract_version") == contract["analysis_quality"]["version"]:
        golden_count = int(contract["html"]["golden_core_chart_count"])
        golden_chart_count_ok = expected_chart_count == golden_count
        if not golden_chart_count_ok:
            errors.append(f"current qualitative contract requires exactly {golden_count} core charts")
    chart_ids = [node.get("data-chart-id", "") for node in chart_nodes]
    nonempty_ids = [value for value in chart_ids if value]
    if nonempty_ids and len(nonempty_ids) != len(set(nonempty_ids)):
        errors.append("chart_id values must be unique")

    chart_metadata_match = True
    metadata_lines = re.findall(
        r"^chart_ready:\s*true\s*;(?P<meta>.*)$",
        markdown_text,
        flags=re.MULTILINE | re.IGNORECASE,
    )
    for index, meta in enumerate(metadata_lines):
        def metadata_value(field: str) -> str:
            match = re.search(rf"(?:^|;)\s*{re.escape(field)}:\s*([^;]+)", meta)
            return match.group(1).strip() if match else ""

        chart_id = metadata_value("chart_id")
        node = soup.select_one(f'[data-chart-id="{chart_id}"]') if chart_id else (
            chart_nodes[index] if index < len(chart_nodes) else None
        )
        if node is None:
            continue
        try:
            payload = json.loads(node.get("data-chart-series", "{}"))
        except json.JSONDecodeError:
            chart_metadata_match = False
            errors.append(f"chart {chart_id or index + 1} has invalid data-chart-series JSON")
            continue
        datasets = {
            str(item.get("label", "")): item
            for item in payload.get("datasets", [])
            if isinstance(item, dict)
        }
        expected_units: dict[str, str] = {}
        for item in re.split(r"[,，]", metadata_value("unit_map")):
            if "=" in item:
                label, unit = item.split("=", 1)
                if label.strip() and unit.strip():
                    expected_units[label.strip()] = unit.strip()
        expected_roles = {
            label.strip(): "bar"
            for label in re.split(r"[,，]", metadata_value("bar_series"))
            if label.strip()
        }
        expected_roles.update({
            label.strip(): "line"
            for label in re.split(r"[,，]", metadata_value("line_series"))
            if label.strip()
        })
        for label, unit in expected_units.items():
            if label not in datasets:
                chart_metadata_match = False
                errors.append(f"chart {chart_id or index + 1} unit_map series missing from rendered data: {label}")
            elif datasets[label].get("unit") != unit:
                chart_metadata_match = False
                errors.append(
                    f"chart {chart_id or index + 1} unit_map mismatch for {label}: "
                    f"expected {unit}, got {datasets[label].get('unit', '')}"
                )
        for label, role in expected_roles.items():
            if label not in datasets:
                chart_metadata_match = False
                errors.append(f"chart {chart_id or index + 1} declared series missing from rendered data: {label}")
            elif datasets[label].get("role") != role:
                chart_metadata_match = False
                errors.append(
                    f"chart {chart_id or index + 1} series role mismatch for {label}: "
                    f"expected {role}, got {datasets[label].get('role', '')}"
                )

    duplicate_ids = [
        value for value in {node.get("id") for node in soup.select("[id]")}
        if value and len(soup.select(f'[id="{value}"]')) > 1
    ]
    if duplicate_ids:
        errors.append("duplicate DOM id values: " + ", ".join(sorted(duplicate_ids)))

    rating = rating_from_markdown(markdown_text)
    components = sorted({node.get("data-component-role") for node in soup.select("[data-component-role]") if node.get("data-component-role")})
    source_structure = report_structure_signature(markdown_text)
    manifest = {
        "schema_version": "1.1",
        "source_markdown": "",
        "rating": rating.display if rating else "legacy",
        "components": components,
        "charts": nonempty_ids or [node.get("data-chart-title", "") for node in chart_nodes],
        "source_structure": source_structure,
        "validation": {
            "dimension_count": len(dimensions),
            "dimension_headings_match": dimension_headings_match,
            "golden_chart_count": golden_chart_count_ok,
            "chart_metadata_match": chart_metadata_match,
            "raw_markdown_absent": raw_markdown_absent,
            "default_open_roles": open_roles,
        },
    }
    return errors, manifest


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate qualitative HTML DOM")
    parser.add_argument("--html", required=True)
    parser.add_argument("--markdown", required=True)
    parser.add_argument("--manifest")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    html_path = Path(args.html).expanduser().resolve()
    markdown_path = Path(args.markdown).expanduser().resolve()
    if not html_path.is_file() or not markdown_path.is_file():
        print("HTML and Markdown inputs must exist")
        return 2
    errors, manifest = validate_html(
        html_path.read_text(encoding="utf-8"),
        markdown_path.read_text(encoding="utf-8"),
    )
    manifest["source_markdown"] = markdown_path.name
    manifest_path = Path(args.manifest).expanduser().resolve() if args.manifest else html_path.parent / "render_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for error in errors:
        print(f"[FAIL] {error}")
    print(f"Render manifest: {manifest_path}")
    print("HTML DOM validation: " + ("PASS" if not errors else "FAIL"))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
