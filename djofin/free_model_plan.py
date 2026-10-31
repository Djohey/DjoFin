"""DjoFin FREE_ONLY model evaluation plan. No model downloads or paid calls are triggered."""
from dataclasses import dataclass
from pathlib import Path
import json
import os

@dataclass(frozen=True)
class FreeOnlyPolicy:
    max_eur: int = 0
    allow_paid_api: bool = False
    allow_live_trades: bool = False
    allow_model_download: bool = False
    allow_gpu_rental: bool = False

POLICY = FreeOnlyPolicy()
CANDIDATES = {
    "minilm": {
        "model_id": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        "purpose": "semantic similarity and deduplication",
        "status": "proposed_not_executed",
    },
    "mdeberta": {
        "model_id": "MoritzLaurer/mDeBERTa-v3-base-mnli-xnli",
        "purpose": "zero-shot classification",
        "status": "proposed_not_executed",
    },
    "finbert": {
        "model_id": "ProsusAI/finbert",
        "purpose": "English financial sentiment, not price prediction",
        "status": "proposed_not_executed",
    },
}

def authorize_operation(*, estimated_eur=0, paid_api=False, live_trade=False,
                        model_download=False, gpu_rental=False):
    if estimated_eur != 0 or paid_api or live_trade or model_download or gpu_rental:
        raise PermissionError("FREE_ONLY: operation blocked until explicit authorization and review")
    return True

def manifest():
    return {"policy": vars(POLICY), "candidates": CANDIDATES,
            "note": "Planning only; no model weights installed or downloaded."}

if __name__ == "__main__":
    print(json.dumps(manifest(), indent=2))
