"""Shared qualitative rating and structured-parameter helpers.

The Markdown validator, renderer and publisher use this module so a report has
one business-quality grade instead of three independently inferred labels.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

try:
    from .report_contract import report_contract
except ImportError:  # pragma: no cover - direct script imports
    from report_contract import report_contract


@dataclass(frozen=True)
class BusinessQualityRating:
    grade: str
    label: str
    outlook: str
    version: str

    @property
    def display(self) -> str:
        base = f"{self.grade} / {self.label}"
        return f"{base} · {self.outlook}" if self.outlook else base


def structured_param(markdown: str, name: str) -> str:
    table_match = re.search(
        rf"\|\s*{re.escape(name)}\s*\|\s*(.+?)\s*\|",
        markdown,
    )
    if table_match:
        return table_match.group(1).strip().strip("`\"'")
    yaml_match = re.search(
        rf"^\s*{re.escape(name)}\s*:\s*(.+?)\s*$",
        markdown,
        flags=re.MULTILINE,
    )
    if yaml_match:
        return yaml_match.group(1).strip().strip("`\"'")
    return ""


def canonical_rating(grade: str, outlook: str = "") -> BusinessQualityRating:
    rating = report_contract("qualitative")["business_quality_rating"]
    grades = rating["grades"]
    normalized_grade = grade.strip().upper()
    if normalized_grade not in grades:
        raise ValueError(f"Unknown business-quality grade: {grade!r}")
    normalized_outlook = outlook.strip()
    if normalized_outlook and normalized_outlook not in rating["outlooks"]:
        raise ValueError(f"Unknown rating outlook: {outlook!r}")
    return BusinessQualityRating(
        grade=normalized_grade,
        label=grades[normalized_grade]["label"],
        outlook=normalized_outlook,
        version=rating["version"],
    )


def rating_from_markdown(markdown: str) -> BusinessQualityRating | None:
    grade = structured_param(markdown, "business_quality_grade")
    if not grade:
        return None
    return canonical_rating(grade, structured_param(markdown, "rating_outlook"))


def rating_errors(markdown: str) -> list[str]:
    fields = {
        name: structured_param(markdown, name)
        for name in (
            "business_quality_grade",
            "business_quality_label",
            "rating_outlook",
            "rating_version",
        )
    }
    missing = [name for name, value in fields.items() if not value]
    if missing:
        return [f"missing rating fields: {', '.join(missing)}"]
    try:
        canonical = canonical_rating(fields["business_quality_grade"], fields["rating_outlook"])
    except ValueError as exc:
        return [str(exc)]
    errors: list[str] = []
    if fields["business_quality_label"] != canonical.label:
        errors.append(
            "business_quality_label does not match grade: "
            f"expected {canonical.label}, got {fields['business_quality_label']}"
        )
    if fields["rating_version"] != canonical.version:
        errors.append(
            f"rating_version must be {canonical.version}, got {fields['rating_version']}"
        )
    first_screen = re.search(
        r"^##\s+(?:Business Quality Verdict.*?|商业质量总体评级.*?)\n(?P<body>.*?)(?=^##\s+|\Z)",
        markdown,
        flags=re.MULTILINE | re.DOTALL,
    )
    if first_screen and canonical.display not in first_screen.group("body"):
        errors.append(f"first-screen rating must display {canonical.display}")
    return errors

