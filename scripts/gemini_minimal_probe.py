"""Manual single-call Gemini connectivity test, without financial data.

No retries. Never print the API key, provider response text, or user data.
Free-tier status must be verified by the owner before dispatch.
"""
import json
import os
import urllib.error
import urllib.request

def main():
    if os.getenv("DJOFIN_FREE_TEST_APPROVED") != "YES" or os.getenv("DJOFIN_FREE_TIER_CONFIRMED") != "YES":
        raise SystemExit("Explicit free-tier approval required")
    key = os.environ["GEMINI_API_KEY"]
    model = "gemini-3.5-flash-lite"
    endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    payload = {"contents": [{"parts": [{"text": "Return exactly one word: OK"}]}],
               "generationConfig": {"maxOutputTokens": 16, "temperature": 0}}
    request = urllib.request.Request(
        endpoint, data=json.dumps(payload).encode("utf-8"),
        headers={"x-goog-api-key": key, "Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            result = json.load(response)
    except urllib.error.HTTPError as exc:
        category = "UNKNOWN"
        reason = "UNCLASSIFIED"
        allowed = {"NOT_FOUND", "INVALID_ARGUMENT", "PERMISSION_DENIED",
                   "UNAUTHENTICATED", "RESOURCE_EXHAUSTED", "FAILED_PRECONDITION",
                   "UNAVAILABLE", "INTERNAL"}
        try:
            body = json.loads(exc.read(8192))
            status = body.get("error", {}).get("status")
            if status in allowed:
                category = status
            message = str(body.get("error", {}).get("message", "")).lower()
            if "not found for api version" in message:
                reason = "MODEL_API_VERSION_MISMATCH"
            elif "not supported for generatecontent" in message:
                reason = "GENERATION_NOT_SUPPORTED"
            elif "not found" in message and "model" in message:
                reason = "MODEL_NOT_FOUND_FOR_GENERATION"
            elif "api key" in message:
                reason = "API_KEY_RESTRICTION"
            elif "location" in message or "region" in message:
                reason = "LOCATION_RESTRICTION"
            elif "billing" in message:
                reason = "BILLING_RESTRICTION"
            elif "permission" in message or "access" in message:
                reason = "ACCESS_RESTRICTION"
        except (ValueError, TypeError, AttributeError):
            pass
        print(json.dumps({"http": exc.code, "error_category": category,
                          "model": model, "reason": reason, "generation_succeeded": False,
                          "usage_known": False, "retry": False}))
        raise SystemExit(1) from None
    usage = result.get("usageMetadata", {})
    print(json.dumps({"http": 200, "model": model, "generation_succeeded": bool(result.get("candidates")),
                      "usage_tokens": {"input": usage.get("promptTokenCount"),
                                       "output": usage.get("candidatesTokenCount"),
                                       "total": usage.get("totalTokenCount")},
                      "billing_verified_by_api": False}))
if __name__ == "__main__":
    main()
