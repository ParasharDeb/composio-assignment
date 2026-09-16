"""
Shared helpers for the research pipeline (agent/research.py, check_urls.py,
critic.py, select_sample.py, diff_passes.py, build_human_check.py, score.py).

Nothing in here modifies research/raw or research/pass1 - those are treated
as read-only source-of-truth for "pass 1".
"""
import csv
import json
import os
import re
import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESEARCH_DIR = ROOT / "research"
DEFAULT_CSV = RESEARCH_DIR / "apps.csv"
DEFAULT_PASS1_DIR = RESEARCH_DIR / "pass1"
DEFAULT_VERIFY_DIR = RESEARCH_DIR / "verify"

APP_SCHEMA_FIELDS = [
    "id", "name", "category", "website", "description", "auth_methods",
    "self_serve", "gating_notes", "api_surface", "api_breadth",
    "mcp_exists", "mcp_notes", "buildability", "blocker", "evidence",
    "confidence",
]

REQUIRED_FIELDS = [
    "id", "name", "auth_methods", "self_serve", "api_surface",
    "mcp_exists", "buildability", "evidence", "confidence",
]

PROMPT_TEMPLATE = """You are researching a single software product/API to assess whether \
Composio (a platform that turns apps into tools AI agents can call) could build an \
agent toolkit for it.

App to research:
- id: {id}
- name: {name}
- category: {category}
- website / hint: {website}

Research this app using ONLY official sources: its own developer docs, API reference, \
pricing/signup pages, and (if needed) its own blog/changelog/status pages. Use WebSearch \
to locate the official docs, then use WebFetch on the actual pages before answering. Do \
not rely on training knowledge alone - every non-obvious claim must be backed by a URL you \
actually fetched in this session.

Fill in exactly this JSON schema (a single JSON object, field names and allowed values exactly \
as shown):

{{
  "id": {id},
  "name": "{name}",
  "category": "{category}",
  "website": "<canonical https:// URL>",
  "description": "<one sentence: what it does>",
  "auth_methods": ["<e.g. OAuth2, API key, Basic Auth, Token/Bearer - be specific>"],
  "self_serve": "self-serve" | "partial" | "gated" | "unknown",
  "gating_notes": "<why: is credential access free/instant, or paid-plan / admin-approval / contact-sales gated? cite specifics>",
  "api_surface": "REST" | "GraphQL" | "REST+GraphQL" | "CLI" | "other" | "unknown",
  "api_breadth": "narrow" | "moderate" | "broad" | "unknown",
  "mcp_exists": true | false,
  "mcp_notes": "<official/community MCP server details, or 'none found'>",
  "buildability": "yes" | "partial" | "no",
  "blocker": "<the main blocker if buildability isn't a clean yes, else 'none'>",
  "evidence": ["<https:// URL you actually fetched, one per major claim>"],
  "confidence": "high" | "medium" | "low"
}}

Rules:
- Use "unknown" (never a guess) for any field the docs don't make clear.
- confidence should reflect how directly the docs supported your answers.
- evidence must be real URLs you fetched/searched in this session, not invented ones.
- Output ONLY the JSON object. No markdown code fences, no commentary before or after.
"""


def slug(name: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return s or "app"


def parse_ids(spec: str):
    ids = set()
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            a, b = part.split("-", 1)
            ids.update(range(int(a), int(b) + 1))
        else:
            ids.add(int(part))
    return ids


def load_app_index(csv_path: Path = DEFAULT_CSV):
    """Reuses research/apps.csv (id,name,category,hint) as the canonical app list."""
    apps = []
    with open(csv_path, "r", encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            apps.append({
                "id": int(row["id"]),
                "name": row["name"],
                "category": row["category"],
                "website": row.get("hint", ""),
            })
    apps.sort(key=lambda a: a["id"])
    return apps


def resolve_selection(only: str, ids_spec: str, app_index):
    selected = set()
    if ids_spec:
        selected |= parse_ids(ids_spec)
    if only:
        wanted = {n.strip().lower() for n in only.split(",") if n.strip()}
        found = {a["name"].lower() for a in app_index}
        missing = wanted - found
        if missing:
            raise SystemExit(f"--only names not found in {DEFAULT_CSV}: {sorted(missing)}")
        for app in app_index:
            if app["name"].lower() in wanted:
                selected.add(app["id"])
    if not selected:
        selected = {a["id"] for a in app_index}
    return sorted(selected)


def find_claude_cli() -> str:
    path = shutil.which("claude")
    if not path:
        raise RuntimeError(
            "claude CLI not found on PATH. Run `claude --version` in this shell to confirm "
            "it's installed (npm i -g @anthropic-ai/claude-code) and on PATH."
        )
    return path


def _build_cmd(claude_path, model, allowed_tools, output_format="json"):
    cmd = [claude_path, "-p", "--model", model, "--output-format", output_format]
    if allowed_tools is not None:
        cmd += ["--allowedTools", allowed_tools]
    if os.name == "nt" and claude_path.lower().endswith((".cmd", ".bat")):
        cmd = ["cmd.exe", "/c"] + cmd
    return cmd


def run_claude(prompt: str, model: str = "sonnet", allowed_tools: str = "WebSearch,WebFetch",
               timeout: int = 240):
    """Runs `claude -p` headless, prompt via stdin, --output-format json.

    Returns (result_text, outer_json) where outer_json is the full CLI response
    envelope (cost, session_id, etc.) and result_text is outer_json["result"].
    """
    claude_path = find_claude_cli()
    cmd = _build_cmd(claude_path, model, allowed_tools)
    proc = subprocess.run(
        cmd, input=prompt, capture_output=True, text=True, timeout=timeout,
        encoding="utf-8", errors="replace",
    )
    if proc.returncode != 0:
        raise RuntimeError(f"claude exited {proc.returncode}: {(proc.stderr or '')[:2000]}")
    try:
        outer = json.loads(proc.stdout)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"claude did not return valid JSON envelope: {e}\nstdout[:500]={proc.stdout[:500]}")
    if outer.get("is_error"):
        raise RuntimeError(f"claude reported an error: {str(outer.get('result'))[:2000]}")
    return outer.get("result", ""), outer


def extract_json(text: str):
    """Best-effort extraction of a JSON object/array from a model response that
    may be wrapped in markdown fences or have stray commentary."""
    t = text.strip()
    t = re.sub(r"^```(?:json)?\s*", "", t)
    t = re.sub(r"\s*```$", "", t)
    t = t.strip()
    try:
        return json.loads(t)
    except json.JSONDecodeError:
        pass
    start_candidates = [i for i in (t.find("{"), t.find("[")) if i != -1]
    if not start_candidates:
        raise ValueError(f"No JSON object/array found in response: {t[:300]!r}")
    start = min(start_candidates)
    end_obj, end_arr = t.rfind("}"), t.rfind("]")
    end = max(end_obj, end_arr)
    if end == -1 or end < start:
        raise ValueError(f"No closing bracket found in response: {t[:300]!r}")
    return json.loads(t[start:end + 1])


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def load_records(path: Path):
    """Loads app records from a single JSON file (list or dict) or a directory
    of JSON files (each a list or a dict), skipping files that start with '_'.
    If a directory contains '_all.json', that file alone is used."""
    path = Path(path)
    if path.is_dir():
        all_json = path / "_all.json"
        if all_json.exists():
            files = [all_json]
        else:
            files = sorted(p for p in path.glob("*.json") if not p.name.startswith("_"))
        records = []
        for f in files:
            with open(f, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            if isinstance(data, list):
                records.extend(data)
            elif isinstance(data, dict):
                records.append(data)
        return records
    else:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        return data if isinstance(data, list) else [data]


def records_by_id(path: Path):
    return {r["id"]: r for r in load_records(path) if "id" in r}


def write_json(path: Path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=2, ensure_ascii=False)
