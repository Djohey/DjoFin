"""Fail-closed historical replay packet builder.

Analyst evidence must be stored separately from evaluator outcomes and audit notes.
This module never reads evaluator or audit directories.
"""
from datetime import datetime, timezone
from hashlib import sha256
import json
import re

class ReplayGateError(ValueError):
    pass

FORBIDDEN = re.compile(r"\b(?:covid[- ]?19|sars[- ]?cov[- ]?2|omicron|sputnik\s*v)\b", re.I)
FIELDS = frozenset({"source_id", "published_utc", "text", "archive_captured_utc", "archive_sha256"})

def utc(value):
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (AttributeError, ValueError) as exc:
        raise ReplayGateError("Invalid timestamp") from exc
    if dt.tzinfo is None:
        raise ReplayGateError("Timezone required")
    return dt.astimezone(timezone.utc)

def build_analyst_packet(case, *, attempt_id):
    if not isinstance(case, dict) or set(case) != {"case_id", "cutoff_utc", "observations"}:
        raise ReplayGateError("Case must contain only whitelisted fields")
    if not isinstance(attempt_id, str) or not attempt_id.strip():
        raise ReplayGateError("Missing attempt ID")
    cutoff = utc(case["cutoff_utc"])
    if cutoff.isoformat() != "2020-01-15T21:00:00+00:00":
        raise ReplayGateError("Cutoff mismatch: approved scenario uses 2020-01-15 21:00 UTC")
    if not isinstance(case["observations"], list) or not case["observations"]:
        raise ReplayGateError("Verified evidence required")
    rows = []
    for row in case["observations"]:
        if not isinstance(row, dict) or set(row) != FIELDS:
            raise ReplayGateError("Observation has forbidden or missing metadata")
        publication = utc(row["published_utc"])
        capture = utc(row["archive_captured_utc"])
        if publication > cutoff or capture > cutoff or capture < publication:
            raise ReplayGateError("Source was not verifiably available by cutoff")
        if not isinstance(row["archive_sha256"], str) or not re.fullmatch("[0-9a-f]{64}", row["archive_sha256"]):
            raise ReplayGateError("Missing archived content digest")
        if not all(isinstance(row[k], str) and row[k].strip() for k in ("source_id", "text")):
            raise ReplayGateError("Invalid observation")
        if FORBIDDEN.search(row["text"]):
            raise ReplayGateError("Anachronistic vocabulary")
        rows.append({"source_id": row["source_id"], "published_utc": publication.isoformat(), "text": row["text"], "archive_sha256": row["archive_sha256"]})
    packet = {"case_id": case["case_id"], "cutoff_utc": cutoff.isoformat(), "attempt_id": attempt_id, "observations": rows}
    if FORBIDDEN.search(json.dumps(packet, ensure_ascii=False)):
        raise ReplayGateError("Anachronistic packet metadata")
    packet["packet_sha256"] = sha256(json.dumps(packet, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()
    return packet
