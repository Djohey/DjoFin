"""Read-only Gemini model discovery. Does not generate content or spend tokens.

Never prints API keys, full response bodies, or private project identifiers.
"""
import json
import os
import urllib.error
import urllib.request

def main():
    if os.environ.get("DJOFIN_FREE_TEST_APPROVED") != "YES":
        raise SystemExit("Manual approval required")
    key = os.environ["GEMINI_API_KEY"]
    url = "https://generativelanguage.googleapis.com/v1beta/models?pageSize=100"
    req = urllib.request.Request(url, headers={"x-goog-api-key": key})
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            data = json.load(response)
    except urllib.error.HTTPError as exc:
        raise SystemExit(f"Model listing failed: HTTP {exc.code}") from None
    models = [
        {"name": m.get("name"), "generateContent": "generateContent" in m.get("supportedGenerationMethods", [])}
        for m in data.get("models", []) if m.get("name", "").startswith("models/gemini-")
    ]
    detail = {}
    for model_name in ("gemini-2.5-flash", "gemini-2.5-flash-lite"):
        url = "https://generativelanguage.googleapis.com/v1beta/models/" + model_name
        request = urllib.request.Request(url, headers={"x-goog-api-key": key})
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                record = json.load(response)
            detail[model_name] = {
                "http": 200,
                "name": record.get("name"),
                "supported_methods": record.get("supportedGenerationMethods", []),
                "input_token_limit": record.get("inputTokenLimit"),
                "output_token_limit": record.get("outputTokenLimit"),
            }
        except urllib.error.HTTPError as exc:
            detail[model_name] = {"http": exc.code}
    print(json.dumps({"model_count": len(models), "model_details": detail}, ensure_ascii=False))
if __name__ == "__main__":
    main()
