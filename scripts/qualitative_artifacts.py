"""Create and validate internal artifacts for the qualitative writing chain."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import jsonschema


SCHEMA_DIR = Path(__file__).resolve().parent.parent / "shared" / "qualitative"
SIDECAR_SCHEMAS = {
    "qualitative_evidence.json": SCHEMA_DIR / "qualitative_evidence_schema.json",
    "qualitative_argument_map.json": SCHEMA_DIR / "qualitative_argument_schema.json",
    "qualitative_content_audit.json": SCHEMA_DIR / "qualitative_content_audit_schema.json",
}


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


def write_chain_prompts(project_root: Path, output_dir: Path, report_path: Path) -> dict[str, Path]:
    evidence_path = output_dir / "qualitative_evidence.json"
    argument_path = output_dir / "qualitative_argument_map.json"
    audit_path = output_dir / "qualitative_content_audit.json"

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
- Choose one explicit SOTP mode and complete all decision fields.
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
- a non-full SOTP mode lacks a concrete decision reason, best feasible analysis, double-counting check or upgrade trigger;
- prose reads like a generated template, repeats headings mechanically, or hides the investment conclusion behind caveats.

Score each dimension 1-5. `pass` requires every score >=4 and no blocking/major finding.
If revision is needed, list only the section headings that may be changed in allowed_revision_sections.
Do not change the report in this step.
"""

    revision_prompt = f"""# Step 5D — Bounded revision

Read {audit_path}, {argument_path}, and {report_path}.
If the audit decision is `revise`, edit only headings named in `allowed_revision_sections`.
Preserve the report's section order, all unaffected prose, and the existing core chart count.
Resolve every blocking/major finding with clearer conclusion, mechanism, counter-evidence and investment implication.
Do not expose internal evidence IDs, prompts, validators, workflow boundaries or source tags such as `[src: ...]`.
If the audit decision is `pass`, do not edit the report.
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
    }
    path = output_dir / "report_provenance.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path

