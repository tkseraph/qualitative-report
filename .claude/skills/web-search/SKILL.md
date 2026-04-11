---
name: web-search
description: Search the web from Claude Code or cc-haha when the built-in WebSearch tool is unavailable or disabled, especially in OpenAI-compatible mode. Use for current documentation, latest versions, recent news, API changes, troubleshooting, release notes, or any task that needs fresh external information. Prefer this skill when you need search strategy, source filtering, or reproducible web research steps.
---

# Web Search

Use this skill when you need fresh information from the public web and the runtime may not expose Claude's native WebSearch tool.

Keep the workflow simple and reproducible.

## Default strategy

1. Clarify the target briefly in your own head: official docs, issue threads, news, release notes, or broad discovery.
2. Prefer official sources first.
3. Use one of the search paths below.
4. Read the most relevant pages.
5. Cross-check important claims with at least 2 sources unless the user only asked for a quick answer.
6. In the final answer, cite sources with titles and URLs.

## Search paths

### Path A, bundled Tavily scripts if API key exists

If `TAVILY_API_KEY` is available, use the bundled Tavily scripts first because they are cleaner and more stable for agent workflows.

Examples:

```bash
node ${CLAUDE_SKILL_DIR}/scripts/search.mjs "site:react.dev useEffect docs"
node ${CLAUDE_SKILL_DIR}/scripts/search.mjs "next.js 2026 release notes" -n 8
node ${CLAUDE_SKILL_DIR}/scripts/search.mjs "OpenAI Responses API tools" --deep
node ${CLAUDE_SKILL_DIR}/scripts/extract.mjs "https://example.com/article"
```

Use `--deep` only for harder research.

### Path B, direct search engine fetch when no API key exists

Use `WebFetch` on search result pages or use `Bash` with `curl` for search pages and then fetch target pages.

Good query patterns:

- Official docs: `site:docs.example.com feature name`
- GitHub issues: `site:github.com/org/repo issue keyword`
- Release notes: `product name release notes 2026`
- Error troubleshooting: `"exact error message"`
- API changes: `product API changelog version`

Useful search URLs:

```text
https://www.google.com/search?q=<query>
https://duckduckgo.com/html/?q=<query>
https://www.bing.com/search?q=<query>
```

If one engine blocks or returns poor results, switch engines.

## Recommended workflow by task

### Official documentation lookup

1. Search with `site:` restriction to the official docs domain.
2. Open the most likely official page.
3. If docs are ambiguous, also check changelog or release notes.
4. Return the answer with links.

### Troubleshooting

1. Search the exact error in quotes.
2. Prefer official docs, GitHub issues, and maintainer discussions.
3. Distinguish workaround vs root-cause fix.
4. Mention version-specific advice.

### Recent news or releases

1. Search for the product plus current year.
2. Prefer official announcements first.
3. Use secondary reporting only to supplement.
4. Call out uncertainty if sources disagree.

## Query writing rules

- Include the current year for recent docs, releases, or news.
- Use exact quotes for error messages.
- Add `site:` whenever you already know the likely authoritative domain.
- Split broad research into 2 to 4 narrower searches instead of one vague query.
- Avoid relying on SEO blogs when primary sources exist.

## Output rules

When reporting back:

- Answer the user's actual question first.
- Then include a `Sources:` section.
- Format sources as markdown links.
- If confidence is limited, say what remains uncertain.

Example:

```markdown
The issue is caused by X, introduced in version Y. The safest fix is Z.

Sources:
- [Official migration guide](https://example.com)
- [GitHub issue discussing the regression](https://github.com/example/repo/issues/123)
```

## Notes for cc-haha

- This skill is meant as a fallback when native `WebSearch` is not available in the current provider mode.
- Prefer the bundled Tavily scripts when configured.
- Otherwise use normal web search plus page fetching.
- The bundled scripts live under `${CLAUDE_SKILL_DIR}/scripts/` so the skill is self-contained inside `~/cc-haha/.claude/skills/web-search/`.
