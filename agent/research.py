"""
Step 1 of the pipeline: research apps by calling Claude Code headless (`claude -p`)
per app, with WebSearch/WebFetch as the only allowed tools.

Usage (PowerShell or bash):
    python agent/research.py --only "Stripe" --out research/_test
    python agent/research.py --ids 1-100 --out research/pass1_rerun
    python agent/research.py --ids 1,50,84 --out research/pass2 --force

Each app is written to its own file in --out (<id>_<slug>.json), so a run is
resumable: re-running with the same --out skips apps that already have a
result file, unless --force is passed. After the run, all present per-app
files in --out are assembled into <out>/_all.json, and a summary of costs /
failures is written to <out>/_run_meta.json.
"""
import argparse
import concurrent.futures as cf
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (  # noqa: E402
    APP_SCHEMA_FIELDS, DEFAULT_CSV, PROMPT_TEMPLATE, REQUIRED_FIELDS, RESEARCH_DIR,
    extract_json, load_app_index, now_iso, resolve_selection, run_claude, slug,
    write_json,
)


def validate(data: dict):
    missing = [f for f in REQUIRED_FIELDS if f not in data]
    if missing:
        raise ValueError(f"response missing required fields: {missing}")
    if not isinstance(data.get("auth_methods"), list):
        raise ValueError("auth_methods must be a list")
    if not isinstance(data.get("evidence"), list) or not data["evidence"]:
        raise ValueError("evidence must be a non-empty list")


def process_app(app, model, allowed_tools, timeout, retries, out_dir):
    prompt = PROMPT_TEMPLATE.format(**app)
    last_err = None
    for attempt in range(1, retries + 2):  # retries=2 -> up to 3 attempts
        try:
            result_text, outer = run_claude(prompt, model=model, allowed_tools=allowed_tools,
                                             timeout=timeout)
            data = extract_json(result_text)
            if isinstance(data, list):  # tolerate a single-element array response
                data = data[0]
            validate(data)
            data["id"] = app["id"]  # id/name/category are ground truth, not the model's to change
            data["name"] = app["name"]
            data["category"] = app["category"]
            data = {k: data.get(k) for k in APP_SCHEMA_FIELDS}
            data["_run"] = {
                "model": model,
                "attempt": attempt,
                "cost_usd": outer.get("total_cost_usd"),
                "duration_ms": outer.get("duration_ms"),
                "session_id": outer.get("session_id"),
                "timestamp": now_iso(),
            }
            out_file = out_dir / f"{app['id']:03d}_{slug(app['name'])}.json"
            write_json(out_file, data)
            return {"id": app["id"], "name": app["name"], "status": "ok",
                     "attempts": attempt, "cost_usd": outer.get("total_cost_usd")}
        except Exception as e:  # noqa: BLE001 - want to retry on anything and report it
            last_err = str(e)
            time.sleep(min(2 ** attempt, 20))
    return {"id": app["id"], "name": app["name"], "status": "failed",
            "attempts": retries + 1, "error": last_err}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--only", help='Comma-separated app names, e.g. "Stripe,Slack"')
    ap.add_argument("--ids", help='Comma/range list of ids, e.g. "1-100" or "1,2,5-10"')
    ap.add_argument("--out", required=True, help="Output directory for this run")
    ap.add_argument("--model", default="sonnet", help="Model alias/name for `claude --model` (default: sonnet)")
    ap.add_argument("--allowed-tools", default="WebSearch,WebFetch",
                     help='--allowedTools value passed to claude (default: "WebSearch,WebFetch")')
    ap.add_argument("--concurrency", type=int, default=4)
    ap.add_argument("--retries", type=int, default=2, help="Extra attempts after the first failure (default: 2)")
    ap.add_argument("--timeout", type=int, default=240, help="Per-attempt subprocess timeout in seconds")
    ap.add_argument("--csv", default=str(DEFAULT_CSV), help="App list CSV (default: research/apps.csv)")
    ap.add_argument("--force", action="store_true", help="Re-run apps even if a cached result file exists")
    args = ap.parse_args()

    app_index = load_app_index(Path(args.csv))
    ids = resolve_selection(args.only, args.ids, app_index)
    by_id = {a["id"]: a for a in app_index}
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    todo, cached = [], []
    for i in ids:
        out_file = out_dir / f"{i:03d}_{slug(by_id[i]['name'])}.json"
        if out_file.exists() and not args.force:
            cached.append(i)
        else:
            todo.append(by_id[i])

    print(f"Selected {len(ids)} app(s). Cached: {len(cached)}. To run: {len(todo)}. "
          f"Model: {args.model}. Concurrency: {args.concurrency}. Out: {out_dir}")

    results = []
    if todo:
        with cf.ThreadPoolExecutor(max_workers=args.concurrency) as ex:
            futs = {ex.submit(process_app, app, args.model, args.allowed_tools, args.timeout,
                               args.retries, out_dir): app for app in todo}
            for fut in cf.as_completed(futs):
                r = fut.result()
                results.append(r)
                if r["status"] == "ok":
                    print(f"  [ok]   {r['id']:03d} {r['name']:<30} "
                          f"${r['cost_usd']:.4f} ({r['attempts']} attempt(s))")
                else:
                    print(f"  [FAIL] {r['id']:03d} {r['name']:<30} {r['error']}")

    # Assemble _all.json from every per-app file currently in out_dir.
    from common import load_records
    all_records = sorted(load_records(out_dir), key=lambda r: r.get("id", 0))
    write_json(out_dir / "_all.json", all_records)

    failed = [r for r in results if r["status"] == "failed"]
    ok = [r for r in results if r["status"] == "ok"]
    total_cost = sum((r.get("cost_usd") or 0) for r in ok)
    meta = {
        "ran_at": now_iso(),
        "model": args.model,
        "requested_ids": ids,
        "ok_count": len(ok),
        "failed_count": len(failed),
        "cached_count": len(cached),
        "total_cost_usd_this_run": round(total_cost, 4),
        "failures": [{"id": r["id"], "name": r["name"], "error": r["error"]} for r in failed],
    }
    write_json(out_dir / "_run_meta.json", meta)

    print(f"\nDone. ok={len(ok)} failed={len(failed)} cached={len(cached)} "
          f"cost_this_run=${total_cost:.4f}")
    print(f"Assembled {len(all_records)} record(s) -> {out_dir / '_all.json'}")
    if failed:
        print(f"FAILED ids: {[r['id'] for r in failed]} - re-run the same command to retry (cache-aware).")
        sys.exit(1)


if __name__ == "__main__":
    main()
