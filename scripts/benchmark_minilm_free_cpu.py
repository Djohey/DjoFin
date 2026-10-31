"""One-shot MiniLM CPU semantic similarity smoke test on existing DjoFin news.

No paid API, no GPU, no trading, no uploads. Model weights are public and
downloaded at runtime to the ephemeral GitHub Actions runner.
This is NOT a quality/accuracy benchmark without independent human labels.
"""
import json
from pathlib import Path

MODEL_ID = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
ROOT = Path(__file__).resolve().parents[1]

def main():
    from sentence_transformers import SentenceTransformer, util
    records = [json.loads(line) for line in (ROOT / "data/news/news.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(records) >= 40, "Need 40 real collected headlines"
    records = records[:40]
    model = SentenceTransformer(MODEL_ID, device="cpu")
    titles = [row["title"] for row in records]
    embeddings = model.encode(titles, convert_to_tensor=True, show_progress_bar=False)
    similarities = util.cos_sim(embeddings, embeddings)
    pairs = []
    for i in range(len(titles)):
        for j in range(i+1, len(titles)):
            score = float(similarities[i,j])
            pairs.append((score,i,j))
    pairs.sort(reverse=True)
    report = {
        "status":"experimental_not_accuracy_validated",
        "model":MODEL_ID, "device":"cpu", "news_count":len(titles),
        "pairs_total":len(pairs),
        "top_10_similar_pairs":[{"score":round(score,5),
             "a_id":records[i]["id"],"a_title":titles[i],
             "b_id":records[j]["id"],"b_title":titles[j]}
             for score,i,j in pairs[:10]],
        "note":"Similarity is not relevance, accuracy, market impact or evidence of learning.",
    }
    print("MINILM_RESULT_JSON_BEGIN")
    print(json.dumps(report,ensure_ascii=False,indent=2))
    print("MINILM_RESULT_JSON_END")

if __name__ == "__main__":
    main()
