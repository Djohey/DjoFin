"""Point-in-time replay isolation: the analyst never receives outcomes or feedback.

This is a data-boundary safeguard, not a guarantee that a pretrained model
has forgotten events from its training data.
"""
from datetime import datetime, timezone
from hashlib import sha256
import json

class ReplayIsolationError(ValueError):
    pass

def _timestamp(value):
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (AttributeError, ValueError) as exc:
        raise ReplayIsolationError("Invalid timestamp") from exc
    if dt.tzinfo is None:
        raise ReplayIsolationError("Timestamp must include timezone")
    return dt.astimezone(timezone.utc)

def build_blind_packet(case, observations, *, attempt_id):
    """Build a fresh, allowlisted packet with only observations public by cutoff.

    Never copy arbitrary fields from case or observations into analyst input.
    Reject future timestamps instead of silently dropping them.
    """
    if not isinstance(case, dict) or not isinstance(attempt_id, str) or not attempt_id.strip():
        raise ReplayIsolationError("Invalid case or attempt")
    if not isinstance(observations, list) or not observations:
        raise ReplayIsolationError("Nonempty observations required")
    cutoff = _timestamp(case["cutoff_utc"])
    clean = []
    for row in observations:
        if not isinstance(row, dict) or set(row) != {"published_utc", "text", "source_id"}:
            raise ReplayIsolationError("Unexpected observation fields")
        published = _timestamp(row["published_utc"])
        if published > cutoff:
            raise ReplayIsolationError("Future information in analyst packet")
        if not isinstance(row["text"], str) or not row["text"].strip():
            raise ReplayIsolationError("Invalid observation text")
        if not isinstance(row["source_id"], str) or not row["source_id"].strip():
            raise ReplayIsolationError("Source id required")
        clean.append({"published_utc": published.isoformat(), "text": row["text"],
                      "source_id": row["source_id"]})
    packet = {"case_id": case["id"], "cutoff_utc": cutoff.isoformat(),
              "attempt_id": attempt_id, "observations": clean,
              "instruction": "Analyze only supplied as-of evidence. Unknown outcomes must remain unknown."}
    packet["packet_sha256"] = sha256(json.dumps(packet, sort_keys=True, ensure_ascii=False,
                                              separators=(",", ":")).encode("utf-8")).hexdigest()
    return packet

def evaluate_blind_attempt(packet, analyst_result, hidden_outcome):
    """Evaluator-only operation. Never feed returned values into replay packets."""
    if not isinstance(packet, dict) or not packet.get("packet_sha256"):
        raise ReplayIsolationError("Invalid packet")
    if not isinstance(analyst_result, dict) or not isinstance(hidden_outcome, dict):
        raise ReplayIsolationError("Invalid evaluation inputs")
    return {"case_id": packet["case_id"], "attempt_id": packet["attempt_id"],
            "packet_sha256": packet["packet_sha256"],
            "analyst_result": analyst_result, "hidden_outcome": hidden_outcome,
            "evaluation_status": "requires_independent_human_or_rubric_review"}
