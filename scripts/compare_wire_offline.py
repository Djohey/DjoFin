"""Print reproducible byte comparison without API calls or secrets."""
import json
from djofin.ai_contract import prepare_request
from djofin.wire_benchmark import compare_wire_formats

def main():
    request = prepare_request(
        [{"observation": "Synthetic example: public ETF daily price jump of 16%; cause not verified",
          "dates": ["2026-10-30"]}],
        snapshot_sha256="a"*64, ticker="CW8.PA",
        as_of_utc="2026-10-31T10:00:00Z", snapshot_dates=["2026-10-30"])
    result = compare_wire_formats(request)
    baseline = result["readable_json_bytes"]
    result["compact_saving_pct"] = round(
        100 * (baseline - result["compact_json_bytes"]) / baseline, 1)
    result["positional_saving_pct"] = round(
        100 * (baseline - result["positional_bytes"]) / baseline, 1)
    result["gemini_calls"] = 0
    print(json.dumps(result, sort_keys=True))

if __name__ == "__main__":
    main()
