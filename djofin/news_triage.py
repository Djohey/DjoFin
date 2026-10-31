"""Offline triage of official RSS archive entries. No claim verification or trades.

An RSS title is a research lead, NEVER a source-content proof.
No network, external API, package installation or automatic hypothesis creation.
"""
from datetime import datetime, timezone
from hashlib import sha256
import json

VERSION = "news-triage-v0.1"
ALLOWED_FEEDS = {"ecb_press": ("finance", "monetary_policy"),
                 "sec_press": ("finance", "regulation")}

def _timestamp(value):
    if not isinstance(value, str):
        raise ValueError("timestamp required")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("invalid timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("timezone required")
    return parsed.astimezone(timezone.utc).isoformat()

def triage_entry(entry):
    """Return a bounded, deterministic research candidate or reject invalid input."""
    if not isinstance(entry, dict):
        raise ValueError("entry must be an object")
    feed = entry.get("feed_id")
    if feed not in ALLOWED_FEEDS:
        raise ValueError("unrecognized feed")
    title, url = entry.get("title"), entry.get("url")
    if not isinstance(title, str) or not title.strip() or len(title) > 2000:
        raise ValueError("invalid title")
    if not isinstance(url, str) or not url.startswith("https://"):
        raise ValueError("invalid HTTPS URL")
    if not isinstance(entry.get("id"), str) or len(entry["id"]) != 64:
        raise ValueError("missing stable RSS id")
    try:
        int(entry["id"], 16)
    except ValueError as exc:
        raise ValueError("invalid RSS id") from exc
    captured = _timestamp(entry.get("fetched_utc"))
    category, topic = ALLOWED_FEEDS[feed]
    return {"version": VERSION, "id": entry["id"], "title": title.strip(),
            "url": url, "feed_id": feed, "captured_at_utc": captured,
            "published_raw": entry.get("published_raw"),
            "category": category, "topic": topic,
            "priority": "review", "source_claim_verified": False,
            "evidence_eligible": False, "investment_signal": False,
            "unknowns": ["full source content not retrieved or checked",
                         "publication time not independently verified",
                         "market relevance and novelty not established"]}

def triage_jsonl(text, *, max_lines=10000):
    if not isinstance(text, str) or len(text.encode("utf-8")) > 900_000:
        raise ValueError("archive exceeds safe size")
    results, seen = [], set()
    for i, line in enumerate(text.splitlines(), 1):
        if i > max_lines:
            raise ValueError("too many entries")
        if not line.strip():
            continue
        entry = json.loads(line)
        candidate = triage_entry(entry)
        if candidate["id"] in seen:
            raise ValueError("duplicate RSS identity")
        seen.add(candidate["id"])
        results.append(candidate)
    results.sort(key=lambda x: (x["captured_at_utc"], x["id"]))
    return {"version": VERSION, "items": results,
            "count": len(results),
            "archive_sha256": sha256(text.encode("utf-8")).hexdigest(),
            "decision": "research_only"}

def json_report(text):
    return json.dumps(triage_jsonl(text), ensure_ascii=False,
                      sort_keys=True, indent=2, allow_nan=False) + "\n"
