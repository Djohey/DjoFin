"""Single-shot Gemini free-tier experiment; never runs automatically.

Requires explicit workflow dispatch and secret. Billing status is not API-verified; owner confirms free tier before dispatch.
"""
import json
import os
import urllib.request
import urllib.error
from djofin.ai_contract import prepare_request, validate_response
from djofin.gemini_adapter import prepare_gemini_payload, extract_gemini_response

def main():
    # Safety: experiment must be explicitly armed in workflow; no implicit retry.
    if os.getenv("DJOFIN_FREE_TEST_APPROVED") != "YES":
        raise SystemExit("Experiment not armed")
    key = os.environ["GEMINI_API_KEY"]
    request = prepare_request(
        [{"observation": "Synthetic example: public ETF daily price jump of 16%; cause not verified",
          "dates": ["2026-10-30"]}],
        snapshot_sha256="a"*64, ticker="CW8.PA",
        as_of_utc="2026-10-31T10:00:00Z", snapshot_dates=["2026-10-30"])
    prepared = prepare_gemini_payload(request, model="gemini-2.5-flash")
    # Free-tier confirmation must be performed by the owner in AI Studio.
    # Never send requests with this script while billing status is uncertain.
    if os.getenv("DJOFIN_FREE_TIER_CONFIRMED") != "YES":
        raise SystemExit("Free tier not confirmed")
    endpoint = ("https://generativelanguage.googleapis.com/v1beta/models/"
                + prepared["model"] + ":generateContent")
    payload = json.dumps(prepared["payload"]).encode()
    http_request = urllib.request.Request(endpoint, data=payload, headers={
        "x-goog-api-key": key, "Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(http_request, timeout=20) as response:
            envelope = json.load(response)
    except urllib.error.HTTPError as exc:
        raise SystemExit(f'Gemini API HTTP {exc.code}; no retry. Check model and quota.') from None
    answer, tokens = extract_gemini_response(envelope)
    verdict = validate_response(request, answer)
    print(json.dumps({"test":"single public synthetic observation",
                      "model":prepared["model"],"tokens":tokens,
                      "contract_valid":verdict["ok"],"flags":verdict["flags"],
                      "billing_verified_by_api":False},ensure_ascii=False))
if __name__ == "__main__":
    main()
