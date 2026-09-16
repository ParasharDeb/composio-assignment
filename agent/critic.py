"""
Step 3: for apps flagged by check_urls.py, ask a stronger model (opus) to
adjudicate - given the pass-1 claim and the flagged URL(s) (with page text),
does it agree or dispute, and what's the corrected value?

Writes one file per reviewed app to research/final/<id>_<slug>.json (the
critic's corrected record + a "_critic" verdict block), and a merged
research/final/apps_final.json = pass-1 baseline for all 100 apps, with
critic corrections applied where an app was reviewed.

Usage:
    python agent/critic.py --flags research/verify/url_flags.json --pass1 research/pass1 --out research/final
"""
import argparse
import concurrent.futures as cf
import sys
import time
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (  # noqa: E402
    APP_SCHEMA_FIELDS, RESEARCH_DIR, extract_json, load_records, now_iso, run_claude,
    slug, write_json,
)

MAX_URLS_PER_APP = 5
SNIPPET_CHARS = 4000

CRITIC_PROMPT = """You are auditing one row of a research dataset about whether an app could \
be turned into an AI-agent toolkit. A first research pass produced the CLAIM below. Some of \
its evidence URLs were auto-flagged (dead link, redirected elsewhere, or the page text doesn't \
obviously mention the claimed auth method) - that does not mean the claim is wrong, only that \
it needs a second look.

CLAIM (from pass 1):
{claim_json}

FLAGGED EVIDENCE (auto-detected issues, plus the fetched page text where available):
{flagged_json}

Your job:
1. For each of these fields - auth_methods, self_serve, gating_notes, api_surface, api_breadth, \
mcp_exists, mcp_notes, buildability, blocker - decide if the pass-1 value holds up given the \
flagged evidence. If the provided page text isn't enough, you may use WebFetch on the flagged \
URL(s) (or a corrected URL you find via the same domain) to confirm.
2. Produce a corrected version of the full record (same schema as the claim). Where you agree \
with pass 1, copy the value through unchanged. Where you disagree, put the corrected value and \
make sure `evidence` reflects a real, working URL.
3. Report which field names you changed.

Output ONLY this JSON object, no markdown fences, no commentary:
{{
  "id": {id},
  "name": "{name}",
  "verdict": "agree" | "dispute",
  "disputed_fields": ["<field names you changed, [] if none>"],
  "notes": "<1-3 sentences on what changed and why, or why the flag was a false positive>",
  "corrected": {{
    "id": {id}, "name": "{name}", "category": "{category}", "website": "...",
    "description": "...", "auth_methods": [...], "self_serve": "...",
    "gating_notes": "...", "api_surface": "...", "api_breadth": "...",
    "mcp_exists": true, "mcp_notes": "...", "buildability": "...", "blocker": "...",
    "evidence": ["..."], "confidence": "high" | "medium" | "low"
  }}
}}
"""


def build_prompt(claim, flagged_entries):
    import json
    trimmed = []
    for e in flagged_entries[:MAX_URLS_PER_APP]:
        trimmed.append({
            "url": e.get("url"),
            "flags": e.get("flags"),
            "status_code": e.get("status_code"),
            "final_url": e.get("final_url"),
            "page_text_snippet": (e.get("page_text_snippet") or "")[:SNIPPET_CHARS],
        })
    claim_for_prompt = {k: claim.get(k) for k in APP_SCHEMA_FIELDS}
    return CRITIC_PROMPT.format(
        claim_json=json.dumps(claim_for_prompt, indent=2),
        flagged_json=json.dumps(trimmed, indent=2),
        id=claim["id"], name=claim["name"], category=claim.get("category", ""),
    )


def review_app(claim, flagged_entries, model, allowed_tools, timeout, retries, out_dir):
    prompt = build_prompt(claim, flagged_entries)
    last_err = None
    for attempt in range(1, retries + 2):
        try:
            result_text, outer = run_claude(prompt, model=model, allowed_tools=allowed_tools, timeout=timeout)
            data = extract_json(result_text)
            if "corrected" not in data or "verdict" not in data:
                raise ValueError(f"critic response missing required keys: {list(data.keys())}")
            corrected = {k: data["corrected"].get(k) for k in APP_SCHEMA_FIELDS}
            corrected["id"] = claim["id"]
            corrected["name"] = claim["name"]
            corrected["category"] = claim.get("category")
            record = dict(corrected)
            record["_critic"] = {
                "verdict": data.get("verdict"),
                "disputed_fields": data.get("disputed_fields", []),
                "notes": data.get("notes"),
                "reviewed_urls": [e.get("url") for e in flagged_entries[:MAX_URLS_PER_APP]],
                "model": model,
                "cost_usd": outer.get("total_cost_usd"),
                "timestamp": now_iso(),
            }
            out_file = out_dir / f"{claim['id']:03d}_{slug(claim['name'])}.json"
            write_json(out_file, record)
            return {"id": claim["id"], "name": claim["name"], "status": "ok",
                     "verdict": data.get("verdict"), "disputed_fields": data.get("disputed_fields", []),
                     "cost_usd": outer.get("total_cost_usd")}
        except Exception as e:  # noqa: BLE001
            last_err = str(e)
            time.sleep(min(2 ** attempt, 20))
    return {"id": claim["id"], "name": claim["name"], "status": "failed", "error": last_err}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--flags", default=str(RESEARCH_DIR / "verify" / "url_flags.json"))
    ap.add_argument("--pass1", default=str(RESEARCH_DIR / "pass1"))
    ap.add_argument("--out", default=str(RESEARCH_DIR / "final"))
    ap.add_argument("--model", default="opus")
    ap.add_argument("--allowed-tools", default="WebFetch")
    ap.add_argument("--concurrency", type=int, default=3)
    ap.add_argument("--retries", type=int, default=2)
    ap.add_argument("--timeout", type=int, default=300)
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    import json
    with open(args.flags, "r", encoding="utf-8") as fh:
        flags_doc = json.load(fh)

    by_app_flags = defaultdict(list)
    for entry in flags_doc["results"]:
        if entry.get("flags"):
            by_app_flags[entry["id"]].append(entry)

    baseline = {r["id"]: r for r in load_records(Path(args.pass1))}
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    flagged_ids = sorted(by_app_flags)
    print(f"{len(flagged_ids)} app(s) have flagged evidence and will be reviewed by {args.model}.")

    todo = []
    skipped = []
    for aid in flagged_ids:
        out_file = out_dir / f"{aid:03d}_{slug(baseline[aid]['name'])}.json"
        if out_file.exists() and not args.force:
            skipped.append(aid)
        else:
            todo.append(aid)

    results = []
    if todo:
        with cf.ThreadPoolExecutor(max_workers=args.concurrency) as ex:
            futs = {
                ex.submit(review_app, baseline[aid], by_app_flags[aid], args.model, args.allowed_tools,
                          args.timeout, args.retries, out_dir): aid
                for aid in todo
            }
            for fut in cf.as_completed(futs):
                r = fut.result()
                results.append(r)
                if r["status"] == "ok":
                    print(f"  [{r['verdict']:7}] {r['id']:03d} {r['name']:<28} "
                          f"disputed={r['disputed_fields']} (${r['cost_usd']:.4f})")
                else:
                    print(f"  [FAIL]    {r['id']:03d} {r['name']:<28} {r['error']}")

    # Assemble the full 100-app "final" dataset: pass1 baseline, overridden by any
    # critic-reviewed record found on disk in out_dir (covers this run + prior runs).
    reviewed = {r["id"]: r for r in load_records(out_dir) if "_critic" in r}
    merged = []
    for aid, base_record in sorted(baseline.items()):
        merged.append(reviewed.get(aid, base_record))
    write_json(out_dir / "apps_final.json", merged)

    disputed = [r for r in reviewed.values() if r["_critic"]["verdict"] == "dispute"]
    summary = {
        "ran_at": now_iso(),
        "model": args.model,
        "flagged_app_count": len(flagged_ids),
        "reviewed_this_run": len(todo),
        "skipped_cached": len(skipped),
        "failed_this_run": len([r for r in results if r["status"] == "failed"]),
        "total_reviewed_on_disk": len(reviewed),
        "disputed_count": len(disputed),
        "agreed_count": len(reviewed) - len(disputed),
        "disputed_apps": [{"id": r["id"], "name": r["name"], "disputed_fields": r["_critic"]["disputed_fields"]}
                           for r in disputed],
        "cost_usd_this_run": round(sum((r.get("cost_usd") or 0) for r in results if r["status"] == "ok"), 4),
    }
    write_json(out_dir / "_critic_summary.json", summary)

    print(f"\nReviewed {len(reviewed)} app(s) total on disk ({len(disputed)} disputed, "
          f"{len(reviewed) - len(disputed)} agreed). Merged final dataset (100 apps) -> "
          f"{out_dir / 'apps_final.json'}")


if __name__ == "__main__":
    main()
