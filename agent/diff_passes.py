"""
Step 4b: for the verification sample, compare pass 1 vs. pass 2 (independent
re-run) vs. final (post-critic) on the 4 fields that matter most for the
deliverable's headline claims: auth method, self-serve/gated access,
API surface + MCP existence, and buildability verdict.

Usage:
    python agent/diff_passes.py
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import DEFAULT_VERIFY_DIR, RESEARCH_DIR, load_records, now_iso, write_json  # noqa: E402

FIELDS = ["auth", "access", "api_mcp", "buildability"]


def field_values(r):
    if r is None:
        return {f: None for f in FIELDS}
    return {
        "auth": ", ".join(r.get("auth_methods") or []) or None,
        "access": r.get("self_serve"),
        "api_mcp": f"{r.get('api_surface')} (mcp={'yes' if r.get('mcp_exists') else 'no'})"
                   if r.get("api_surface") is not None else None,
        "buildability": r.get("buildability"),
    }


def norm(v):
    return (v or "").strip().lower()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sample", default=str(DEFAULT_VERIFY_DIR / "sample_ids.json"))
    ap.add_argument("--pass1", default=str(RESEARCH_DIR / "pass1"))
    ap.add_argument("--pass2", default=str(RESEARCH_DIR / "pass2"))
    ap.add_argument("--final", default=str(RESEARCH_DIR / "final"))
    ap.add_argument("--out", default=str(DEFAULT_VERIFY_DIR / "diff.json"))
    args = ap.parse_args()

    import json
    with open(args.sample, "r", encoding="utf-8") as fh:
        sample = json.load(fh)
    sample_ids = sample["all_ids"]

    pass1 = {r["id"]: r for r in load_records(Path(args.pass1))}
    pass2_dir = Path(args.pass2)
    pass2 = {r["id"]: r for r in load_records(pass2_dir)} if pass2_dir.exists() else {}
    final_dir = Path(args.final)
    final_all = final_dir / "apps_final.json"
    if final_all.exists():
        final = {r["id"]: r for r in load_records(final_all)}
    elif final_dir.exists():
        final = {r["id"]: r for r in load_records(final_dir)}
    else:
        final = {}

    rows = []
    agreement = {f: {"p1_vs_p2": 0, "p1_vs_final": 0, "p2_vs_final": 0, "n": 0} for f in FIELDS}

    for aid in sample_ids:
        name = pass1.get(aid, pass2.get(aid, {})).get("name", f"app-{aid}")
        v1 = field_values(pass1.get(aid))
        v2 = field_values(pass2.get(aid))
        vf = field_values(final.get(aid) or pass1.get(aid))  # unreviewed apps: final falls back to pass1
        for field in FIELDS:
            row = {
                "id": aid, "name": name, "field": field,
                "pass1": v1[field], "pass2": v2[field], "final": vf[field],
                "pass1_vs_pass2_match": norm(v1[field]) == norm(v2[field]) if v2[field] is not None else None,
                "pass1_vs_final_match": norm(v1[field]) == norm(vf[field]),
                "pass2_vs_final_match": (norm(v2[field]) == norm(vf[field])) if v2[field] is not None else None,
            }
            rows.append(row)
            agreement[field]["n"] += 1
            if row["pass1_vs_pass2_match"]:
                agreement[field]["p1_vs_p2"] += 1
            if row["pass1_vs_final_match"]:
                agreement[field]["p1_vs_final"] += 1
            if row["pass2_vs_final_match"]:
                agreement[field]["p2_vs_final"] += 1

    out = {
        "generated_at": now_iso(),
        "sample_ids": sample_ids,
        "n_apps": len(sample_ids),
        "n_pass2_available": len(pass2),
        "n_final_reviewed": len([aid for aid in sample_ids if aid in final]),
        "field_agreement": agreement,
        "rows": rows,
    }
    write_json(Path(args.out), out)

    print(f"{len(sample_ids)} sample apps; pass2 available for {len(pass2)}; "
          f"final (critic-reviewed) for {out['n_final_reviewed']}.")
    for f in FIELDS:
        a = agreement[f]
        print(f"  {f:<12} pass1==pass2: {a['p1_vs_p2']}/{a['n']}   pass1==final: {a['p1_vs_final']}/{a['n']}")
    print(f"Written -> {args.out}")


if __name__ == "__main__":
    main()
