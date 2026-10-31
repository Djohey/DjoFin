"""Gemini experimental adapter: public market-data analyst only.

Offline preparation only. No HTTP calls, no credentials, no access to source code
or databases. Live integration requires separate explicit approval.
"""
import json
from djofin.ai_contract import serialize_request

GEMINI_ROLE = (
    "You are a read-only analyst of PUBLIC market observations. "
    "Assess data quality and uncertainty, not investments. "
    "Do not suggest trades, change data, or request secrets. "
    "Return strictly JSON matching the supplied response contract."
)

class GeminiPreparationError(ValueError):
    pass

def prepare_gemini_payload(request, *, model="gemini-2.5-flash-lite"):
    """Build minimal Gemini generateContent payload; does not send anything."""
    if not isinstance(model, str) or not model.startswith("gemini-"):
        raise GeminiPreparationError("Explicit Gemini model required")
    if not isinstance(request, dict) or not request.get("request_digest"):
        raise GeminiPreparationError("Validated request required")
    # Only the contracted, filtered observations; never attach repository files.
    prompt = serialize_request(request)
    payload = {
        "system_instruction": {"parts": [{"text": GEMINI_ROLE}]},
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0,
            "maxOutputTokens": 600,
        },
    }
    return {"model": model, "payload": payload, "network_enabled": False,
            "estimated_input_bytes": len(prompt.encode("utf-8"))}

def extract_gemini_response(envelope):
    """Extract JSON and usage metadata from a Gemini response, offline."""
    try:
        candidate = envelope["candidates"][0]
        parts = candidate["content"]["parts"]
        text = "".join(p["text"] for p in parts)
        answer = json.loads(text)
        usage = envelope.get("usageMetadata", {})
        tokens = {
            "input": int(usage.get("promptTokenCount", 0)),
            "output": int(usage.get("candidatesTokenCount", 0)),
            "total": int(usage.get("totalTokenCount", 0)),
            "thoughts": int(usage.get("thoughtsTokenCount", 0)),
            "cached": int(usage.get("cachedContentTokenCount", 0)),
        }
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        raise GeminiPreparationError("Malformed Gemini response") from exc
    if any(v < 0 for v in tokens.values()):
        raise GeminiPreparationError("Negative token usage")
    return answer, tokens
