"""
Merge per-category research output (research/raw/*.json) into a single
dataset (research/apps.json) and compute pattern statistics (research/patterns.json).

Run after all category research agents have written their files:
    python research/merge.py
"""
import json
import glob
from collections import Counter, defaultdict
import os

RAW_DIR = os.path.join(os.path.dirname(__file__), "raw")
OUT_APPS = os.path.join(os.path.dirname(__file__), "apps.json")
OUT_PATTERNS = os.path.join(os.path.dirname(__file__), "patterns.json")

def load_all():
    apps = []
    files = sorted(glob.glob(os.path.join(RAW_DIR, "*.json")))
    for f in files:
        with open(f, "r", encoding="utf-8") as fh:
            data = json.load(fh)
            if not isinstance(data, list):
                raise ValueError(f"{f} did not contain a JSON array")
            apps.extend(data)
    apps.sort(key=lambda a: a.get("id", 0))
    return apps, files

def normalize_auth(method_text):
    """Bucket a free-text auth method string into a small taxonomy."""
    t = method_text.lower()
    if "unknown" in t:
        return None
    if "oauth" in t:
        return "OAuth2"
    if "api key" in t or "apikey" in t or "x-api-key" in t or "clay-api-key" in t:
        return "API key"
    if "basic auth" in t:
        return "Basic Auth"
    if "none" in t or "local" in t or "cli" in t:
        return "None / local (CLI tool)"
    if "token" in t or "jwt" in t or "session" in t:
        return "Token / Bearer"
    return "Other"

def compute_patterns(apps):
    total = len(apps)
    auth_counter = Counter()  # per-app, deduped bucket set
    for a in apps:
        buckets = set()
        for m in a.get("auth_methods", []):
            b = normalize_auth(m)
            if b:
                buckets.add(b)
        for b in buckets:
            auth_counter[b] += 1

    self_serve_counter = Counter(a.get("self_serve", "unknown") for a in apps)
    buildability_counter = Counter(a.get("buildability", "unknown") for a in apps)
    mcp_counter = Counter(bool(a.get("mcp_exists")) for a in apps)

    by_category = defaultdict(lambda: Counter())
    for a in apps:
        by_category[a.get("category", "unknown")][a.get("self_serve", "unknown")] += 1

    blocker_counter = Counter(
        a.get("blocker", "none") for a in apps if a.get("blocker") and a.get("blocker").lower() != "none"
    )

    def tier(a):
        ss, bd = a.get("self_serve"), a.get("buildability")
        if ss == "self-serve" and bd == "yes":
            return "easy_win"
        if bd == "no" or ss == "gated":
            return "needs_outreach"
        return "partial"

    easy_wins = [a["name"] for a in apps if tier(a) == "easy_win"]
    partial = [a["name"] for a in apps if tier(a) == "partial"]
    needs_outreach = [a["name"] for a in apps if tier(a) == "needs_outreach"]

    return {
        "total_apps": total,
        "auth_method_counts": dict(auth_counter.most_common()),
        "self_serve_counts": dict(self_serve_counter.most_common()),
        "buildability_counts": dict(buildability_counter.most_common()),
        "mcp_exists_count": mcp_counter.get(True, 0),
        "self_serve_by_category": {k: dict(v) for k, v in by_category.items()},
        "top_blockers": dict(blocker_counter.most_common(10)),
        "easy_wins": easy_wins,
        "partial": partial,
        "needs_outreach": needs_outreach,
    }

def main():
    apps, files = load_all()
    with open(OUT_APPS, "w", encoding="utf-8") as fh:
        json.dump(apps, fh, indent=2)
    patterns = compute_patterns(apps)
    with open(OUT_PATTERNS, "w", encoding="utf-8") as fh:
        json.dump(patterns, fh, indent=2)
    print(f"Merged {len(apps)} apps from {len(files)} files -> {OUT_APPS}")
    print(f"Patterns written -> {OUT_PATTERNS}")
    missing_ids = sorted(set(range(1, 101)) - set(a.get("id") for a in apps))
    if missing_ids:
        print(f"WARNING: missing app ids: {missing_ids}")

if __name__ == "__main__":
    main()
