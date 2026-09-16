"""
Step 6: read research/verify/human_check.csv (after a human has filled in the
"truth" column) and compute pass-1 vs. final accuracy against that ground
truth, plus the list of misses - i.e. the actual "accuracy moved from a lower
first pass to a higher one" evidence for the case study.

Rows with a blank "truth" are not yet verified and are excluded from scoring.

Usage:
    python agent/score.py
"""
import argparse
import csv
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import DEFAULT_VERIFY_DIR, now_iso, write_json  # noqa: E402

WS_RE = re.compile(r"\s+")


def normalize(s):
    return WS_RE.sub(" ", (s or "").strip().lower())


def loose_match(value, truth):
    nv, nt = normalize(value), normalize(truth)
    if not nv or not nt:
        return None
    return nv == nt or nv in nt or nt in nv


def pct(n, d):
    return round(100.0 * n / d, 1) if d else None


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--in", dest="in_path", default=str(DEFAULT_VERIFY_DIR / "human_check.csv"))
    ap.add_argument("--out", default=str(DEFAULT_VERIFY_DIR / "accuracy.json"))
    args = ap.parse_args()

    with open(args.in_path, "r", encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))

    scored = [r for r in rows if r.get("truth", "").strip()]
    by_field = {}
    misses_pass1, misses_final, improved, regressed = [], [], [], []

    for r in scored:
        field = r["field"]
        by_field.setdefault(field, {"n": 0, "pass1_correct": 0, "final_correct": 0})
        p1_ok = loose_match(r["pass1"], r["truth"])
        f_ok = loose_match(r["final"], r["truth"])
        by_field[field]["n"] += 1
        if p1_ok:
            by_field[field]["pass1_correct"] += 1
        else:
            misses_pass1.append(r)
        if f_ok:
            by_field[field]["final_correct"] += 1
        else:
            misses_final.append(r)
        if not p1_ok and f_ok:
            improved.append(r)
        if p1_ok and not f_ok:
            regressed.append(r)

    n_total = len(scored)
    n_pass1_correct = sum(v["pass1_correct"] for v in by_field.values())
    n_final_correct = sum(v["final_correct"] for v in by_field.values())

    out = {
        "generated_at": now_iso(),
        "n_total_rows": len(rows),
        "n_scored": n_total,
        "n_unscored_pending_truth": len(rows) - n_total,
        "pass1_accuracy_pct": pct(n_pass1_correct, n_total),
        "final_accuracy_pct": pct(n_final_correct, n_total),
        "by_field": {
            field: {
                "n": v["n"],
                "pass1_accuracy_pct": pct(v["pass1_correct"], v["n"]),
                "final_accuracy_pct": pct(v["final_correct"], v["n"]),
            }
            for field, v in by_field.items()
        },
        "improved_by_verification": improved,  # pass1 wrong, final right - the verification loop's payoff
        "regressed_by_verification": regressed,  # pass1 right, final wrong - critic made it worse
        "still_wrong_in_final": misses_final,
        "wrong_in_pass1": misses_pass1,
    }
    write_json(Path(args.out), out)

    if n_total == 0:
        print(f"0/{len(rows)} rows have a 'truth' value filled in yet - fill in {args.in_path} by hand, "
              f"then re-run this script.")
    else:
        print(f"Scored {n_total}/{len(rows)} rows.")
        print(f"  pass1 accuracy: {out['pass1_accuracy_pct']}%   final accuracy: {out['final_accuracy_pct']}%")
        print(f"  improved by verification: {len(improved)}   regressed: {len(regressed)}")
    print(f"Written -> {args.out}")


if __name__ == "__main__":
    main()
