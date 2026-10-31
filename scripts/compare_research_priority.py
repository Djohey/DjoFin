"""Compare stable v0.1 and candidate v0.2 on real collected news, without promoting either."""
import json
from collections import Counter
from pathlib import Path
from djofin import research_priority as stable
from djofin import research_priority_v02 as candidate

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/news/news.jsonl"
DEST = ROOT / "data/audit/research_priority_v01_v02_comparison.json"

def main():
    items = [json.loads(line) for line in SOURCE.read_text(encoding="utf-8").splitlines() if line.strip()]
    comparisons = []
    for item in items:
        old = stable.classify(item)
        new = candidate.classify(item)
        comparisons.append({
            "id": item["id"], "feed_id": item.get("feed_id"),
            "title": item.get("title"), "v01": {"priority":old["priority"],"domains":old["domains"]},
            "v02": {"priority":new["priority"],"domains":new["domains"],"matched_terms":new["matched_terms"],
                    "triggers":new["triggers"],"negated_triggers":new["negated_triggers"]},
            "priority_changed": old["priority"] != new["priority"],
            "domains_changed": old["domains"] != new["domains"],
        })
    report = {
        "status":"candidate_comparison_only_not_accuracy_validation",
        "items":len(comparisons),
        "v01_counts":dict(sorted(Counter(x["v01"]["priority"] for x in comparisons).items())),
        "v02_counts":dict(sorted(Counter(x["v02"]["priority"] for x in comparisons).items())),
        "priority_changed":sum(x["priority_changed"] for x in comparisons),
        "domains_changed":sum(x["domains_changed"] for x in comparisons),
        "v02_rules_sha256":candidate.RULES_SHA256,
        "caveat":"All 40 news items may have influenced previous rule discussions; this is not an independent holdout.",
        "items_detail":comparisons,
    }
    DEST.parent.mkdir(parents=True,exist_ok=True)
    DEST.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in report.items() if k!="items_detail"},indent=2))

if __name__=="__main__":
    main()
