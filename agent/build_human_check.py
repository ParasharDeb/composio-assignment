"""
Step 5: write research/verify/human_check.csv - one row per (app, field) for
the 20-app verification sample, with pass1 and final values side by side and
a blank "truth" column for a human to fill in by hand against the live docs.

Usage:
    python agent/build_human_check.py
"""
import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import DEFAULT_VERIFY_DIR, RESEARCH_DIR, load_records  # noqa: E402
from diff_passes import FIELDS, field_values  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sample", default=str(DEFAULT_VERIFY_DIR / "sample_ids.json"))
    ap.add_argument("--pass1", default=str(RESEARCH_DIR / "pass1"))
    ap.add_argument("--final", default=str(RESEARCH_DIR / "final"))
    ap.add_argument("--out", default=str(DEFAULT_VERIFY_DIR / "human_check.csv"))
    args = ap.parse_args()

    import json
    with open(args.sample, "r", encoding="utf-8") as fh:
        sample = json.load(fh)
    sample_ids = sample["all_ids"]

    pass1 = {r["id"]: r for r in load_records(Path(args.pass1))}
    final_dir = Path(args.final)
    final_all = final_dir / "apps_final.json"
    if final_all.exists():
        final = {r["id"]: r for r in load_records(final_all)}
    elif final_dir.exists():
        final = {r["id"]: r for r in load_records(final_dir)}
    else:
        final = {}

    rows = []
    for aid in sample_ids:
        p1 = pass1.get(aid)
        f_rec = final.get(aid) or p1
        v1, vf = field_values(p1), field_values(f_rec)
        source_url = (f_rec.get("evidence") or p1.get("evidence") or [""])[0]
        for field in FIELDS:
            rows.append({
                "app": p1["name"],
                "field": field,
                "pass1": v1[field] or "",
                "final": vf[field] or "",
                "truth": "",
                "source_url": source_url,
            })

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["app", "field", "pass1", "final", "truth", "source_url"])
        w.writeheader()
        w.writerows(rows)

    print(f"Wrote {len(rows)} rows ({len(sample_ids)} apps x {len(FIELDS)} fields) -> {out_path}")
    print("Fill in the 'truth' column by hand against the live docs, then run agent/score.py.")


if __name__ == "__main__":
    main()
