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
    model = "gemini-2.5-flash"
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
        allowed = {"NOT_FOUND", "INVALID_ARGUMENT", "PERMISSION_DENIED",
                   "UNAUTHENTICATED", "RESOURCE_EXHAUSTED", "FAILED_PRECONDITION",
                   "UNAVAILABLE", "INTERNAL"}
        try:
            body = json.loads(exc.read(8192))
            status = body.get("error", {}).get("status")
            if status in allowed:
                category = status
        except (ValueError, TypeError, AttributeError):
            pass
        print(json.dumps({"http": exc.code, "error_category": category,
                          "model": model, "generation_succeeded": False,
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
