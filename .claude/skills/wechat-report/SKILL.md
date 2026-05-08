---
name: wechat-report
description: Create WeChat Official Account draft-box entries from finished Turtle Investment Framework Markdown reports using npx @lyhue1991/wxgzh. Draft-only; does not publish or store credentials.
---

# wechat-report

Use this skill when the user wants to turn a finished Turtle Investment Framework Markdown report into a WeChat Official Account draft-box entry.

## Scope

This skill only creates draft-box drafts. It does not publish, submit, mass-send, or schedule articles.

Use it for:

- Finished `*_qualitative_report.md`, `*_turtle_report.md`, or `*_valuation_report.md` reports.
- Local output directories that already pass `scripts/validate_reports.py`.
- Creating a draft the user will review and publish manually in the WeChat Official Account backend.

Do not use it for:

- Formal publishing, mass sending, or automatic release.
- Reports that have not been generated yet.
- Reports that fail validator checks.
- Storing or collecting AppID, AppSecret, tokens, or account credentials.

## Prerequisites

The user must configure these outside this project:

- Node.js and `npx`.
- WeChat Official Account developer access.
- WeChat API IP allowlist / interface permissions required by `wxgzh`.
- `@lyhue1991/wxgzh` account configuration or environment variables.

Do not write credentials into this repository.

## Standard workflow

1. Validate the output directory or report file first:

   ```bash
   PYTHONPATH=scripts .venv/bin/python scripts/validate_reports.py output/688668_dingtong_e2e_fresh
   ```

2. Dry-run the draft command:

   ```bash
   PYTHONPATH=scripts .venv/bin/python scripts/wechat_report.py output/688668_dingtong_e2e_fresh --type turtle --dry-run
   ```

3. Ask the user to confirm they want to create a WeChat draft.

4. Only after confirmation, create the draft with `--yes`:

   ```bash
   PYTHONPATH=scripts .venv/bin/python scripts/wechat_report.py output/688668_dingtong_e2e_fresh --type turtle --account turtle --theme blue --yes
   ```

5. Tell the user to inspect and publish manually from the WeChat Official Account backend.

## CLI reference

Examples:

```bash
PYTHONPATH=scripts .venv/bin/python scripts/wechat_report.py output/688668_dingtong_e2e_fresh --type turtle --dry-run
PYTHONPATH=scripts .venv/bin/python scripts/wechat_report.py output/688668_dingtong_e2e_fresh --type valuation --account turtle --theme blue --yes
PYTHONPATH=scripts .venv/bin/python scripts/wechat_report.py output/688668_dingtong_e2e_fresh --file output/688668_dingtong_e2e_fresh/688668_SH_turtle_report.md --author "龟龟投资框架" --dry-run
```

Supported options:

- `path`: output directory or Markdown report file.
- `--type qualitative|turtle|valuation`: report type when `path` is a directory.
- `--file PATH`: explicit Markdown report file.
- `--account NAME`, `--author TEXT`, `--digest TEXT`, `--theme NAME`, `--cover PATH`, `--no-cover`: passed through to `wxgzh`.
- `--output-dir PATH`: defaults to `<report_dir>/.wxgzh`.
- `--skip-validation`: skip report validator only if the user explicitly requests it.
- `--dry-run`: print the `npx` command without network/API calls.
- `--yes`: required for real draft creation.

## Safety rules

- Never run commands containing `publish`, `submit`, `mass`, or similar release actions.
- Never accept or store `--appid`, `--appsecret`, `--secret`, `--token`, or credential-like arguments.
- Prefer `--dry-run` before any real draft creation.
- Real draft creation must include `--yes` and explicit user confirmation.
- Formal publication must happen manually in the WeChat backend.

## Troubleshooting

- `npx` not found: ask the user to install Node.js locally.
- `wxgzh` configuration missing: ask the user to configure `@lyhue1991/wxgzh` outside this repo.
- IP allowlist error: ask the user to update the WeChat Official Account IP whitelist.
- Permission error: confirm the Official Account has the required draft/material API permissions.
- Validator failure: fix the report content first; do not draft an unfinished report by default.
