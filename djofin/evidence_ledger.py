"""DjoFin research evidence ledger v0.1: offline, deterministic, auditable.

Records hypotheses and evidence without pretending to verify source claims.
No network, model API, investment recommendation or live order.
"""
from datetime import datetime, timezone
from hashlib import sha256
import json

VERSION = "evidence-ledger-v0.1"
STANCES = {"supports", "contradicts", "context"}
STATUSES = {"open", "under_review", "rejected", "validated_for_research"}

def _digest(value):
    return sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                             separators=(",", ":"), allow_nan=False).encode()).hexdigest()

def _utc(value):
    if not isinstance(value, str):
        raise ValueError("timestamp must be an ISO datetime")
    try:
        date = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("invalid ISO datetime") from exc
    if date.tzinfo is None or date.utcoffset() is None:
        raise ValueError("timezone is mandatory")
    return date.astimezone(timezone.utc).isoformat()

def new_hypothesis(identifier, claim, created_at, status="open"):
    if not isinstance(identifier, str) or not identifier.strip():
        raise ValueError("identifier required")
    if not isinstance(claim, str) or len(claim.strip()) < 15:
        raise ValueError("claim must be meaningful")
    if status not in STATUSES:
        raise ValueError("unknown status")
    record = {"id": identifier.strip(), "claim": claim.strip(),
              "created_at_utc": _utc(created_at), "status": status,
              "version": VERSION, "evidence": []}
    record["digest"] = _digest(record)
    return record

def add_evidence(record, *, source_url, published_at, captured_at, stance,
                 excerpt, source_sha256, note=""):
    if not isinstance(record, dict) or record.get("version") != VERSION:
        raise ValueError("unknown ledger")
    current = dict(record)
    old_digest = current.pop("digest", None)
    if old_digest != _digest(current):
        raise ValueError("ledger tampering detected")
    if stance not in STANCES:
        raise ValueError("invalid stance")
    if not isinstance(source_url, str) or not source_url.startswith("https://"):
        raise ValueError("HTTPS source URL required")
    if not isinstance(source_sha256, str) or len(source_sha256) != 64 or any(
            c not in "0123456789abcdef" for c in source_sha256):
        raise ValueError("source content SHA-256 required")
    if not isinstance(excerpt, str) or not excerpt.strip():
        raise ValueError("nonempty excerpt required")
    published, captured = _utc(published_at), _utc(captured_at)
    if published > captured:
        raise ValueError("cannot capture before publication")
    evidence = {"source_url": source_url, "published_at_utc": published,
                "captured_at_utc": captured, "stance": stance,
                "excerpt": excerpt.strip(), "source_sha256": source_sha256,
                "note": str(note)}
    evidence["id"] = _digest(evidence)
    existing = current["evidence"]
    if any(e["id"] == evidence["id"] for e in existing):
        raise ValueError("duplicate evidence")
    updated = {**current, "evidence": existing + [evidence]}
    updated["digest"] = _digest(updated)
    return updated

def review(record):
    copy = dict(record)
    digest = copy.pop("digest", None)
    if digest != _digest(copy):
        raise ValueError("ledger tampering detected")
    counts = {s: sum(e["stance"] == s for e in record["evidence"]) for s in sorted(STANCES)}
    return {"hypothesis_id": record["id"], "status": record["status"],
            "counts": counts, "has_contradiction": counts["contradicts"] > 0,
            "unknowns": ["source content not independently verified",
                         "no demonstrated predictive market impact"],
            "investment_signal": False, "ledger_digest": digest}
