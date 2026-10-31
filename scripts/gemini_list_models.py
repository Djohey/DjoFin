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
    print(json.dumps({"model_count": len(models), "models": models}, ensure_ascii=False))
if __name__ == "__main__":
    main()
