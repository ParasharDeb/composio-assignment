"""
Step 4a: pick the 20-app verification sample - 10 named "trickiest" apps
(low self-serve signal, ambiguous product identity, or thin docs in pass 1)
plus 10 random apps for an unbiased check - and write research/verify/sample_ids.json.

Usage:
    python agent/select_sample.py
"""
import argparse
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import DEFAULT_CSV, DEFAULT_VERIFY_DIR, load_app_index, now_iso, write_json  # noqa: E402

TRICKY_NAMES = [
    "fanbasis", "Paygent Connect", "iPayX", "Waterfall.io", "Sherlock",
    "NotebookLM", "PitchBook", "DealCloud", "Gladly", "Consensus",
]
SEED = 42


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--csv", default=str(DEFAULT_CSV))
    ap.add_argument("--out", default=str(DEFAULT_VERIFY_DIR / "sample_ids.json"))
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--n-random", type=int, default=10)
    args = ap.parse_args()

    app_index = load_app_index(Path(args.csv))
    name_to_id = {a["name"].lower(): a["id"] for a in app_index}

    tricky_ids = []
    missing = []
    for name in TRICKY_NAMES:
        aid = name_to_id.get(name.lower())
        if aid is None:
            missing.append(name)
        else:
            tricky_ids.append(aid)
    if missing:
        raise SystemExit(f"TRICKY_NAMES not found in {args.csv} (check spelling): {missing}")

    remaining = [a["id"] for a in app_index if a["id"] not in tricky_ids]
    rng = random.Random(args.seed)
    random_ids = sorted(rng.sample(remaining, args.n_random))

    all_ids = sorted(set(tricky_ids) | set(random_ids))
    id_to_name = {a["id"]: a["name"] for a in app_index}

    out = {
        "generated_at": now_iso(),
        "seed": args.seed,
        "tricky": [{"id": i, "name": id_to_name[i]} for i in sorted(tricky_ids)],
        "random": [{"id": i, "name": id_to_name[i]} for i in random_ids],
        "all_ids": all_ids,
    }
    write_json(Path(args.out), out)
    print(f"Tricky ({len(tricky_ids)}): {[id_to_name[i] for i in sorted(tricky_ids)]}")
    print(f"Random ({len(random_ids)}, seed={args.seed}): {[id_to_name[i] for i in random_ids]}")
    print(f"Total sample: {len(all_ids)} apps -> {args.out}")


if __name__ == "__main__":
    main()
