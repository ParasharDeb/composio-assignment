# Composio App Research — Take-Home

Research pipeline that evaluates 100 apps for agent-toolkit buildability: auth
method, self-serve vs. gated access, API surface, existing MCP support, and a
buildability verdict with evidence — clustered into patterns, then verified
against real docs.

## What's here

- `task.md` — the assignment brief and the 100-app list.
- `research/raw/*.json` — per-category research output, one file per category
  (10 apps each), produced by parallel research agents.
- `research/merge.py` — merges `raw/*.json` into `research/apps.json` and
  computes `research/patterns.json` (auth distribution, self-serve/gated by
  category, blockers, easy wins vs. needs-outreach).
- `research/verify/` — the verification pass: an independent second research
  pass on a sample of apps, diffed against pass 1, plus manual spot-checks.
- `case-study.html` — the single-page deliverable (findings, patterns, agent
  writeup, verification results).

## How the research agent works

Each of the 100 apps was assigned to one of 10 category-agents (one per
category in `task.md`, 10 apps each), run in parallel. Each agent:

1. Fetches the app's real docs/developer pages directly (WebFetch), falling
   back to a targeted web search when the direct fetch didn't have what was
   needed.
2. Extracts: category, one-line description, auth method(s), self-serve vs.
   gated verdict (with the reason), API surface (REST/GraphQL/CLI/none) and
   breadth, whether an MCP server exists, buildability verdict + blocker, and
   the evidence URL(s) it actually used.
3. Marks its own confidence (high/medium/low), and writes "unknown" rather
   than guessing when the docs didn't make something clear.
4. Writes a structured JSON array to `research/raw/<category>.json`.

Where the agent could not determine something (behind a login wall, contact-
sales-only page, contradictory docs), it's marked `unknown` / low confidence
and called out on the case study page rather than silently guessed.

## Verification

A random stratified sample (~12–15 apps across categories/auth types) was
independently re-researched by a second pass and diffed against pass 1;
disagreements were adjudicated by hand against the live docs. The case study
page shows pass-1 vs. post-verification accuracy on the sample, with the
specific hits and misses — not just a summary number.

## Running it yourself

Requirements: Python 3.9+, a Claude Code / Claude agent environment with
WebFetch + WebSearch (this was run via Claude Code agents, not a standalone
script — see `research/raw/*.json` for the raw output of each category run).

```bash
python research/merge.py     # merge raw/*.json -> apps.json + patterns.json
```

To re-run research for a category, re-prompt an agent with the same schema
used in `research/raw/<category>.json` (see the prompts used in this
project's Claude Code session) and overwrite that file, then re-run
`merge.py`.

## Honesty notes

- No paid accounts were used. Apps gated behind payment, admin approval, or
  contact-sales are reported as gated, with the evidence for that, not
  skipped.
- Where the agent got something wrong or couldn't resolve it, it's shown on
  the case study page, not hidden.
