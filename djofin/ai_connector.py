"""Opt-in, read-only AI transport. No network call unless explicitly enabled.

Uses an OpenAI-compatible chat-completions endpoint; no model provider is
endorsed. Callers must supply only vetted, non-sensitive market observations.
"""
import hashlib
import json
import os
from pathlib import Path
import urllib.request
from urllib.parse import urlparse

from djofin.ai_contract import serialize_request, validate_response, ContractError

MAX_REQUEST_USD = 0.0  # Phase simulation : aucun appel facturable autorise
MAX_RESPONSE_BYTES = 100_000

class ConnectorError(RuntimeError):
    pass

def run_analysis(request, *, transport=None, log_path="sortie/ai_audit.jsonl"):
    """Return validated response. Never writes prices, orders or strategies.

    Cost cap is an *estimate*, not a provider-enforced spending limit.
    """
    if os.environ.get("DJOFIN_AI_ENABLED") != "1":
        raise ConnectorError("AI disabled: set DJOFIN_AI_ENABLED=1 explicitly")
    endpoint = os.environ.get("DJOFIN_AI_ENDPOINT", "")
    parsed = urlparse(endpoint)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise ConnectorError("HTTPS endpoint required")
    if parsed.hostname in {"localhost", "127.0.0.1", "::1"} or parsed.hostname.endswith(".local"):
        raise ConnectorError("Local endpoints forbidden")
    key = os.environ.get("DJOFIN_AI_API_KEY")
    model = os.environ.get("DJOFIN_AI_MODEL")
    if not key or not model:
        raise ConnectorError("API key and model required")
    try:
        input_price = float(os.environ["DJOFIN_AI_INPUT_USD_PER_M"])
        output_price = float(os.environ["DJOFIN_AI_OUTPUT_USD_PER_M"])
    except (KeyError, ValueError) as exc:
        raise ConnectorError("Explicit token prices required") from exc
    if not (0 <= input_price <= 1000 and 0 <= output_price <= 1000):
        raise ConnectorError("Invalid token prices")
    prompt = serialize_request(request)
    # Conservative preflight estimate: UTF-8 bytes per token, plus output allowance.
    max_output_tokens = 600
    estimated_input_tokens = len(prompt.encode("utf-8")) + 1500
    ceiling = (estimated_input_tokens * input_price + max_output_tokens * output_price) / 1_000_000
    if ceiling > MAX_REQUEST_USD:
        raise ConnectorError("Zero-dollar budget: paid AI requests forbidden")
    payload = json.dumps({
        "model": model,
        "temperature": 0,
        "max_tokens": max_output_tokens,
        "messages": [
            {"role": "system", "content": "You are a read-only market data quality analyst. Return only JSON. Never give trading instructions."},
            {"role": "user", "content": prompt},
        ],
    }).encode("utf-8")
    http_request = urllib.request.Request(endpoint, data=payload, headers={
        "Authorization": "Bearer " + key, "Content-Type": "application/json"
    }, method="POST")
    sender = transport or (lambda req: urllib.request.urlopen(req, timeout=20))
    try:
        with sender(http_request) as response:
            raw = response.read(MAX_RESPONSE_BYTES + 1)
        if len(raw) > MAX_RESPONSE_BYTES:
            raise ConnectorError("Response too large")
        envelope = json.loads(raw)
        content = envelope["choices"][0]["message"]["content"]
        answer = json.loads(content)
        verdict = validate_response(request, answer)
    except (ValueError, KeyError, IndexError, TypeError, OSError, ContractError) as exc:
        raise ConnectorError("Model response invalid or unavailable") from exc
    # Append only identifiers and validation flags; never log key, raw prompt or response.
    audit = {
        "request_digest": request["request_digest"],
        "model": model,
        "response_sha256": hashlib.sha256(raw).hexdigest(),
        "validated": verdict["ok"],
        "flags": verdict["flags"],
        "estimated_cost_ceiling_usd": round(ceiling, 8),
    }
    path = Path(log_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as out:
        out.write(json.dumps(audit, ensure_ascii=False) + "\n")
    return {"answer": answer, "validation": verdict, "audit": audit}
