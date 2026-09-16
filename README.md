# Composio App Research — Take-Home

Research pipeline evaluating 100 apps for agent-toolkit buildability: auth
method, self-serve vs. gated access, API surface, existing MCP support, and a
buildability verdict with evidence.

Live page: https://composio-assignment-three.vercel.app/

## Pipeline

**Pass 1 (interactive).** `research/raw/*.json` — one file per category (10
categories, 10 apps each), produced by running Claude Code agents
interactively, one per category. `research/merge.py` merges `raw/*.json`
into `research/apps.json` and computes `research/patterns.json` (auth
distribution, self-serve/gated by category, blockers, easy-wins vs.
needs-outreach).

**Scripted research agent.** `agent/research.py` — calls Claude Code headless
(`claude -p`, restricted to `WebSearch`/`WebFetch`) once per app and writes a
validated JSON record per app. Resumable: re-running with the same `--out`
skips apps that already have a result file.

**URL checking.** `agent/check_urls.py` — fetches every evidence URL from a
research pass and flags HTTP errors, redirects to a homepage/different
domain, or pages whose text doesn't mention the claimed auth method. This
flagged 54/100 apps.

**Critic review.** `agent/critic.py` — for apps flagged by `check_urls.py`,
asks a stronger model (opus) to review the claim against the flagged
evidence and either confirm or correct it. 24 of the 54 flagged apps were
reviewed; output goes to `research/final/`.

**Sampling and diffing.** `agent/select_sample.py` picks a 20-app
verification sample (10 "tricky" apps + 10 random); `agent/diff_passes.py`
runs an independent second research pass (`research/pass2/`) on that sample
and diffs it against pass 1 and the critic-reviewed final.

**Human verification.** `research/verify/human_check.csv` — a verifier agent
is required to quote the live docs for every answer it gives; a human then
reviews each quote against the source and fills in the `truth` column.

**Scoring.** `agent/score.py` — reads `human_check.csv` once `truth` is
filled in and computes pass-1 vs. final accuracy against it.

**Deliverable.** `build_site.py` inlines `research/apps.json` and
`research/patterns.json` into `site/index.html`, the single-page site above.

## How to run

```bash
pip install requests

# scripted research agent, one app
python agent/research.py --only "Notion" --out research/_test

# check evidence URLs for HTTP/redirect/auth-keyword issues
python agent/check_urls.py --in research/pass1 --out research/verify/url_flags.json

# critic review of specific flagged apps (or all flagged apps if --ids omitted)
python agent/critic.py --ids 1-10

# score pass-1 vs. final against research/verify/human_check.csv
python agent/score.py
```

Requires [Claude Code](https://claude.com/claude-code) installed and logged
in on the machine running `agent/research.py` / `agent/critic.py` — no API
key needed, since both call the `claude` CLI headlessly.

## Results

On the 32-row verification sample (8 apps × 4 fields — LiveAgent, Gladly,
fanbasis, Sherlock, Waterfall.io, Paygent Connect, PitchBook, NotebookLM):

- Pass 1 (research agent): **78%** (25/32)
- After critic, no quote requirement: **75%** (24/32)
- After a quote-required verifier + human review: **100%** (32/32)

The unquoted critic pass made things *worse* — it broke 2 answers that pass 1
had gotten right. Requiring the verifier to quote the live docs for every
answer, then having a human check those quotes, fixed all 9 misses.

## Honesty and limits

- Pass 1 was run interactively (one Claude Code agent per category), not via
  a scripted loop — `agent/research.py` exists for re-running or extending
  it, but the original 100-app pass 1 predates it.
- The critic only reviewed 24 of the 54 apps `check_urls.py` flagged; the
  other 30 flagged apps still carry their unreviewed pass-1 values.
- The accuracy numbers above come from an 8-app, 32-row sample, not the full
  100 apps — treat them as directional, not a dataset-wide error rate.
- Paygent Connect's site (pay-gent.com) never returned enough content to
  determine its auth method, access model, or API surface with any
  confidence — it's recorded as `unknown` rather than guessed.
