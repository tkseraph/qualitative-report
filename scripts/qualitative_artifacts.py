"""Create and validate internal artifacts for the qualitative writing chain."""

from __future__ import annotations

import hashlib
import json
import re
import shlex
import sys
from pathlib import Path

import jsonschema


SCHEMA_DIR = Path(__file__).resolve().parent.parent / "shared" / "qualitative"
SIDECAR_SCHEMAS = {
    "qualitative_evidence.json": SCHEMA_DIR / "qualitative_evidence_schema.json",
    "qualitative_argument_map.json": SCHEMA_DIR / "qualitative_argument_schema.json",
    "qualitative_content_audit.json": SCHEMA_DIR / "qualitative_content_audit_schema.json",
}


def report_structure_signature(markdown_text: str) -> dict[str, object]:
    """Return the report skeleton that bounded revisions must preserve."""
    h2_headings = [
        re.sub(r"\s+", " ", heading).strip()
        for heading in re.findall(r"^##\s+(.+?)\s*$", markdown_text, flags=re.MULTILINE)
    ]
    chart_metadata = []
    for line in re.findall(
        r"^chart_ready:\s*true\s*;.*$",
        markdown_text,
        flags=re.MULTILINE | re.IGNORECASE,
    ):
        fields = {
            key.strip(): value.strip()
            for key, value in (
                segment.split(":", 1)
                for segment in line.split(";")
                if ":" in segment
            )
        }
        chart_metadata.append({
            "chart_id": fields.get("chart_id", ""),
            "chart_target": fields.get("chart_target", ""),
        })
    stable_payload = {
        "h2_headings": h2_headings,
        "charts": chart_metadata,
    }
    digest = hashlib.sha256(
        json.dumps(stable_payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return {
        "schema_version": "1.0",
        **stable_payload,
        "h2_count": len(h2_headings),
        "chart_count": len(chart_metadata),
        "sha256": digest,
    }


def write_structure_snapshot(markdown_path: Path, output_path: Path) -> Path:
    signature = report_structure_signature(markdown_path.read_text(encoding="utf-8"))
    signature["source_markdown"] = markdown_path.name
    output_path.write_text(
        json.dumps(signature, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return output_path


def compare_structure_snapshot(markdown_path: Path, snapshot_path: Path) -> list[str]:
    expected = json.loads(snapshot_path.read_text(encoding="utf-8"))
    actual = report_structure_signature(markdown_path.read_text(encoding="utf-8"))
    errors: list[str] = []
    for field, label in (
        ("h2_headings", "H2 section order"),
        ("charts", "chart IDs / targets / order"),
    ):
        if expected.get(field) != actual.get(field):
            errors.append(f"{label} changed during bounded revision")
    return errors


def validate_json_artifact(path: Path, schema_path: Path) -> list[str]:
    if not path.is_file():
        return [f"missing artifact: {path.name}"]
    try:
        instance = json.loads(path.read_text(encoding="utf-8"))
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        return [f"invalid JSON in {path.name}: {exc}"]
    validator = jsonschema.Draft202012Validator(schema)
    return [
        f"{path.name}:{'/'.join(str(part) for part in error.path) or '$'}: {error.message}"
        for error in sorted(validator.iter_errors(instance), key=lambda item: list(item.path))
    ]


def validate_sidecars(output_dir: Path, names: tuple[str, ...]) -> list[str]:
    errors: list[str] = []
    for name in names:
        errors.extend(validate_json_artifact(output_dir / name, SIDECAR_SCHEMAS[name]))
    return errors


def validate_current_argument_quality(path: Path) -> list[str]:
    """Enforce the v2.1 reasoning fields without invalidating legacy sidecars."""
    if not path.is_file():
        return [f"missing artifact: {path.name}"]
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        return [f"invalid JSON in {path.name}: {exc}"]
    checks = payload.get("quality_checks")
    if not isinstance(checks, dict):
        return [f"{path.name}:quality_checks: required by analysis contract 2.1"]
    required = {
        "working_capital_cash_bridge",
        "competing_moat_hypotheses",
        "cycle_transmission",
        "roe_history",
        "sotp_economic_separability",
    }
    missing = sorted(required - set(checks))
    errors = [f"{path.name}:quality_checks: missing {name}" for name in missing]
    hypotheses = checks.get("competing_moat_hypotheses")
    if not isinstance(hypotheses, list) or len(hypotheses) < 2:
        errors.append(f"{path.name}:quality_checks: at least two moat hypotheses required")
    roe = checks.get("roe_history")
    if isinstance(roe, dict):
        years = roe.get("years")
        if isinstance(years, int) and years < 5 and roe.get("five_year_avg") is not None:
            errors.append(f"{path.name}:quality_checks: five_year_avg must be null when years < 5")
    return errors


def write_chain_prompts(project_root: Path, output_dir: Path, report_path: Path) -> dict[str, Path]:
    evidence_path = output_dir / "qualitative_evidence.json"
    argument_path = output_dir / "qualitative_argument_map.json"
    audit_path = output_dir / "qualitative_content_audit.json"
    structure_script = project_root / "scripts" / "qualitative_structure.py"
    structure_snapshot = output_dir / "pre_revision_structure.json"
    capture_structure_command = shlex.join([
        sys.executable,
        str(structure_script),
        "--capture",
        "--report",
        str(report_path),
        "--snapshot",
        str(structure_snapshot),
    ])
    check_structure_command = shlex.join([
        sys.executable,
        str(structure_script),
        "--check",
        "--report",
        str(report_path),
        "--snapshot",
        str(structure_snapshot),
    ])

    evidence_prompt = f"""# Step 5A — Evidence ledger and argument map

Read only these research inputs:
- {output_dir / 'qualitative_input_manifest.json'}
- {output_dir / 'data_pack_market.md'}
- {output_dir / 'computed_metrics.md'}
- {output_dir / 'data_pack_report.md'}
- {output_dir / 'peer_evidence.md'}
- {output_dir / 'pdf_sections.json'}

First write {evidence_path} against:
{SCHEMA_DIR / 'qualitative_evidence_schema.json'}

Then write {argument_path} against:
{SCHEMA_DIR / 'qualitative_argument_schema.json'}

Rules:
- Every conclusion links to evidence IDs; every material contradiction remains visible.
- Overall quality uses the canonical letter / Chinese mapping in shared/report_contract.json.
- D2 must contain mechanism, counter-evidence and failure signals, not just labels.
- D1 must separate operating-asset occupation from operating-liability financing and reconcile cash improvement through receivables, inventory, payables and contract liabilities.
- D2 must compare at least two falsifiable moat hypotheses and use peers as potential counter-evidence, not only support.
- Order-cycle businesses must map customer capex/demand through orders, delivery, acceptance, revenue and cash.
- Choose one explicit SOTP mode and complete all decision fields.
- Test economic separability before SOTP depth: customers, technology, shared resources, cash flow, debt, capex and internal transactions.
- A true `roe_5y_avg` requires five complete annual observations; otherwise keep it null and record available-history coverage.
- Complete `quality_checks` in the argument map for all five current-contract checks, using `not_applicable` only with a company-specific reason.
- These files are internal provenance. Do not put internal evidence IDs or workflow instructions in the public report.
"""

    review_prompt = f"""# Step 5C — Independent semantic content review

Act as a skeptical research editor. Read:
- {report_path}
- {evidence_path}
- {argument_path}
- {output_dir / 'data_pack_report.md'}
- {output_dir / 'peer_evidence.md'}

Write only {audit_path}, conforming to:
{SCHEMA_DIR / 'qualitative_content_audit_schema.json'}

This is not a keyword checklist. Reject the draft if any of these is true:
- a reader cannot state the company essence, real advantage, largest constraint and rating boundary;
- a conclusion describes results but not the causal mechanism;
- D2's six-step interrogation or falsification table lacks a synthesis that weighs competing hypotheses;
- support is listed without explaining why it does not justify a higher rating;
- contract liabilities are added to receivables or inventory and mislabeled as capital occupied;
- a working-capital bridge mixes parent-company and consolidated figures, mixes periods, or includes trade notes on only one side when both sides are material;
- OCF improvement or deterioration is asserted from selected balance-sheet movements alone, without distinguishing customer/supplier financing from collections and checking direct-method cash receipts and payments when disclosed;
- D2 does not compare at least two competing moat hypotheses or ignores a peer counterexample;
- an order-cycle company lacks the demand/capex → order → delivery → acceptance → revenue → cash transmission and a stated current stage;
- a non-full SOTP mode lacks a concrete decision reason, best feasible analysis, double-counting check or upgrade trigger;
- SOTP depth is decided only by data availability without testing economic separability;
- fewer than five annual ROE observations are described as a five-year average;
- prose reads like a generated template, repeats headings mechanically, or hides the investment conclusion behind caveats.

Before passing, perform a table-to-prose delta check for D1-D6: in every dimension, identify at least one prose conclusion that adds a causal mechanism, competing explanation, rating effect or concrete decision beyond merely restating the nearest table. If any dimension only paraphrases its tables, record a major finding. Award `prose_naturalness=5` only when transitions and conclusions are company-specific and varied rather than repeated formula prefixes.

Score each dimension 1-5. `pass` requires every score >=4 and no blocking/major finding.
If revision is needed, list only the section headings that may be changed in allowed_revision_sections.
Do not change the report in this step.
"""

    revision_prompt = f"""# Step 5D — Bounded revision

Read {audit_path}, {argument_path}, and {report_path}.
Before editing, capture the structure baseline:
{capture_structure_command}
If the audit decision is `revise`, edit only headings named in `allowed_revision_sections`.
Preserve the report's section order, all unaffected prose, and the existing core chart count.
Resolve every blocking/major finding with clearer conclusion, mechanism, counter-evidence and investment implication.
Do not expose internal evidence IDs, prompts, validators, workflow boundaries or source tags such as `[src: ...]`.
If the audit decision is `pass`, do not edit the report.
After editing, require this check to pass:
{check_structure_command}
"""

    prompts = {
        "step5_evidence_argument_prompt.md": evidence_prompt,
        "step5_content_review_prompt.md": review_prompt,
        "step5_targeted_revision_prompt.md": revision_prompt,
    }
    paths: dict[str, Path] = {}
    for name, content in prompts.items():
        path = output_dir / name
        path.write_text(content.rstrip() + "\n", encoding="utf-8")
        paths[name] = path
    return paths


def write_provenance(output_dir: Path, report_path: Path) -> Path:
    evidence_path = output_dir / "qualitative_evidence.json"
    argument_path = output_dir / "qualitative_argument_map.json"
    inputs: dict[str, str] = {}
    for name in (
        "annual_report.pdf",
        "data_pack_market.md",
        "computed_metrics.md",
        "data_pack_report.md",
        "peer_evidence.md",
        "qualitative_evidence.json",
        "qualitative_argument_map.json",
    ):
        path = output_dir / name
        if path.is_file():
            inputs[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    evidence_count = 0
    if evidence_path.is_file():
        evidence_count = len(json.loads(evidence_path.read_text(encoding="utf-8")).get("evidence", []))
    payload = {
        "schema_version": "1.0",
        "report": report_path.name,
        "input_sha256": inputs,
        "evidence_count": evidence_count,
        "argument_map": argument_path.name,
        "public_report_contains_internal_evidence_ids": False,
        "report_structure": report_structure_signature(
            report_path.read_text(encoding="utf-8")
        ),
    }
    path = output_dir / "report_provenance.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path
