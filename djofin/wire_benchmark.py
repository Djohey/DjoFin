"""Offline comparison of three Gemini wire formats, with no API calls.

Byte counts are not token counts; no format is promoted without live quality checks.
"""
import json
from djofin.ai_contract import serialize_request, canonical_json

FIELDS = ("schema_version", "mission", "ticker", "as_of_utc",
          "snapshot_sha256", "previous_snapshot_sha256", "alerts",
          "allowed_checks", "permissions", "request_digest")
ALERT_FIELDS = ("id", "observation", "dates")

def pack_positional(request):
    """Experimental wire format: header names are supplied once per message."""
    serialize_request(request)  # validate digest before transformation
    values = [request[key] for key in FIELDS]
    values[6] = [[alert[key] for key in ALERT_FIELDS] for alert in request["alerts"]]
    return canonical_json({"fields": FIELDS, "alert_fields": ALERT_FIELDS, "values": values})

def unpack_positional(wire):
    obj = json.loads(wire)
    if not isinstance(obj, dict) or set(obj) != {"fields", "alert_fields", "values"}:
        raise ValueError("Malformed positional format")
    if tuple(obj["fields"]) != FIELDS or tuple(obj["alert_fields"]) != ALERT_FIELDS:
        raise ValueError("Unexpected field dictionary")
    values = obj["values"]
    if not isinstance(values, list) or len(values) != len(FIELDS):
        raise ValueError("Unexpected field count")
    request = dict(zip(FIELDS, values))
    alerts = request["alerts"]
    if not isinstance(alerts, list):
        raise ValueError("Malformed alerts")
    if any(not isinstance(row, list) or len(row) != len(ALERT_FIELDS) for row in alerts):
        raise ValueError("Malformed alert fields")
    request["alerts"] = [dict(zip(ALERT_FIELDS, row)) for row in alerts]
    serialize_request(request)  # reject tampered digest
    return request

def compare_wire_formats(request):
    readable = serialize_request(request)
    compact = canonical_json(request)
    positional = pack_positional(request)
    if json.loads(readable) != json.loads(compact) or unpack_positional(positional) != request:
        raise ValueError("Wire-format round trip failed")
    return {"readable_json_bytes": len(readable.encode("utf-8")),
            "compact_json_bytes": len(compact.encode("utf-8")),
            "positional_bytes": len(positional.encode("utf-8")),
            "note": "Bytes only; token count and analysis quality not measured."}
