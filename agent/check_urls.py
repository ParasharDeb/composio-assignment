"""
Step 2: fetch every evidence URL for a results dir and flag:
  - HTTP errors (4xx/5xx)
  - redirects to a homepage (or a different domain entirely)
  - pages that don't mention the claimed auth method anywhere in their text

This is a heuristic first pass to point the critic (and a human) at the URLs
worth re-checking - it does not itself decide right/wrong.

Usage:
    python agent/check_urls.py --in research/pass1 --out research/verify/url_flags.json
"""
import argparse
import concurrent.futures as cf
import html
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import DEFAULT_VERIFY_DIR, load_records, now_iso, write_json  # noqa: E402

UA = "Mozilla/5.0 (compatible; ComposioResearchVerifier/1.0; +https://composio.dev)"

AUTH_KEYWORD_RULES = [
    (re.compile(r"oauth"), {"oauth"}),
    (re.compile(r"api[\s\-]?key"), {"api key", "apikey", "api-key", "x-api-key"}),
    (re.compile(r"basic auth"), {"basic auth", "basic authentication"}),
    (re.compile(r"hmac"), {"hmac"}),
    (re.compile(r"jwt"), {"jwt"}),
    (re.compile(r"bearer|token|session"), {"token", "bearer"}),
    (re.compile(r"none|local|cli"), set()),  # nothing to check on page for local/CLI tools
]

TAG_RE = re.compile(r"<(script|style)[^>]*>.*?</\1>", re.IGNORECASE | re.DOTALL)
ANY_TAG_RE = re.compile(r"<[^>]+>")
WS_RE = re.compile(r"\s+")


def strip_html(raw_html: str) -> str:
    t = TAG_RE.sub(" ", raw_html)
    t = ANY_TAG_RE.sub(" ", t)
    t = html.unescape(t)
    return WS_RE.sub(" ", t).strip()


def keywords_for_auth(auth_methods):
    kws = set()
    joined = " ".join(auth_methods or []).lower()
    for pattern, keywords in AUTH_KEYWORD_RULES:
        if pattern.search(joined):
            kws |= keywords
    return kws


def is_homepage_path(path: str) -> bool:
    return path in ("", "/")


def check_one(app, url, timeout):
    entry = {"id": app.get("id"), "name": app.get("name"), "url": url, "flags": []}
    try:
        resp = requests.get(url, timeout=timeout, headers={"User-Agent": UA}, allow_redirects=True)
    except Exception as e:  # noqa: BLE001
        entry["flags"].append("fetch_error")
        entry["error"] = str(e)[:300]
        return entry

    entry["status_code"] = resp.status_code
    entry["final_url"] = resp.url
    if resp.status_code >= 400:
        entry["flags"].append(f"http_{resp.status_code}")

    orig_parsed, final_parsed = urlparse(url), urlparse(resp.url)
    if orig_parsed.netloc.lower().lstrip("www.") != final_parsed.netloc.lower().lstrip("www."):
        entry["flags"].append("redirected_domain_change")
    elif not is_homepage_path(orig_parsed.path) and is_homepage_path(final_parsed.path):
        entry["flags"].append("redirected_to_homepage")

    if resp.ok and "text/html" in resp.headers.get("Content-Type", ""):
        text = strip_html(resp.text)
        text_lower = text.lower()
        kws = keywords_for_auth(app.get("auth_methods"))
        if kws and not any(k in text_lower for k in kws):
            entry["flags"].append("auth_method_not_mentioned")
        entry["page_text_snippet"] = text[:6000]
    return entry


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--in", dest="in_path", required=True, help="Results dir or file to check (e.g. research/pass1)")
    ap.add_argument("--out", default=str(DEFAULT_VERIFY_DIR / "url_flags.json"))
    ap.add_argument("--concurrency", type=int, default=8)
    ap.add_argument("--timeout", type=int, default=15)
    args = ap.parse_args()

    records = load_records(Path(args.in_path))
    tasks = []
    for app in records:
        for url in app.get("evidence") or []:
            tasks.append((app, url))

    print(f"Loaded {len(records)} app record(s) from {args.in_path}; {len(tasks)} evidence URL(s) to check "
          f"(concurrency={args.concurrency}).")

    results = []
    with cf.ThreadPoolExecutor(max_workers=args.concurrency) as ex:
        futs = [ex.submit(check_one, app, url, args.timeout) for app, url in tasks]
        for i, fut in enumerate(cf.as_completed(futs), 1):
            r = fut.result()
            results.append(r)
            tag = f"[{','.join(r['flags'])}]" if r["flags"] else "[clean]"
            print(f"  ({i}/{len(tasks)}) {r['id']:>3} {r['name']:<28} {tag} {r['url']}")

    results.sort(key=lambda r: (r["id"], r["url"]))
    flagged = [r for r in results if r["flags"]]
    flagged_app_ids = sorted({r["id"] for r in flagged})

    out = {
        "checked_at": now_iso(),
        "source": args.in_path,
        "total_urls_checked": len(results),
        "flagged_url_count": len(flagged),
        "flagged_app_ids": flagged_app_ids,
        "flag_type_counts": {},
    }
    for r in results:
        for f in r["flags"]:
            out["flag_type_counts"][f] = out["flag_type_counts"].get(f, 0) + 1
    out["results"] = results

    write_json(Path(args.out), out)
    print(f"\n{len(flagged)}/{len(results)} URL(s) flagged across {len(flagged_app_ids)} app(s).")
    print(f"Flag types: {out['flag_type_counts']}")
    print(f"Written -> {args.out}")


if __name__ == "__main__":
    main()
