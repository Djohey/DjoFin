"""Point-in-time lexical novelty and honest research-alert evaluation.

Offline stdlib. Lexical similarity is NOT economic novelty or alpha.
Historical candidates must have been observed strictly before evaluation cutoff.
"""
from datetime import datetime, timezone
from collections import Counter
import math
import re
from djofin.news_triage import triage_entry

VERSION="novelty-evaluation-v0.1"
WORDS=re.compile(r"(?u)\b\w{3,}\b")
STOP={"the","and","for","with","from","this","that","are","has","have",
      "les","des","une","dans","pour","avec","sur","par","aux","est"}

def _date(value):
    if not isinstance(value,str):raise ValueError("ISO datetime required")
    try:d=datetime.fromisoformat(value.replace("Z","+00:00"))
    except ValueError as e:raise ValueError("invalid datetime") from e
    if d.tzinfo is None or d.utcoffset() is None:raise ValueError("timezone required")
    return d.astimezone(timezone.utc)

def _tokens(title):
    return set(WORDS.findall(title.casefold()))-STOP

def novelty(candidate, historical, *, cutoff_utc, max_history=5000):
    """Jaccard novelty against earlier *observed* headlines, never future data."""
    current=triage_entry(candidate)
    cutoff=_date(cutoff_utc)
    observed=_date(current["captured_at_utc"])
    if observed>cutoff:raise ValueError("candidate unavailable at cutoff")
    if not isinstance(historical,list) or len(historical)>max_history:
        raise ValueError("invalid historical sample")
    seen=set()
    maximum=0.0
    matches=[]
    current_tokens=_tokens(current["title"])
    for item in historical:
        old=triage_entry(item)
        old_date=_date(old["captured_at_utc"])
        if old_date>=observed or old_date>cutoff:
            raise ValueError("future or same-time history: look-ahead risk")
        if old["id"] in seen:raise ValueError("duplicate historical item")
        seen.add(old["id"])
        tokens=_tokens(old["title"])
        union=current_tokens|tokens
        similarity=len(current_tokens&tokens)/len(union) if union else 1.0
        if similarity>maximum:
            maximum=similarity
            matches=[old["id"]]
        elif similarity==maximum and similarity>0:
            matches.append(old["id"])
    return {"version":VERSION,"news_id":current["id"],
            "cutoff_utc":cutoff.isoformat(),
            "lexical_novelty":round(1-maximum,6) if historical else None,
            "nearest_prior_ids":sorted(matches) if historical else [],
            "history_count":len(historical),"market_novelty_verified":False,
            "investment_signal":False,
            "unknowns":["semantic and economic novelty unverified",
                        "source publication timing not independently verified",
                        "news may have been known to market before collection"]}

def evaluate_alerts(predictions,labels,*,cutoff_utc):
    """Evaluate frozen pre-outcome binary alerts vs independent adjudicated labels.

    labels: id -> {positive: bool, adjudicated_at_utc: str}.
    Missing labels are excluded and reported; never silently negative.
    """
    cutoff=_date(cutoff_utc)
    if not isinstance(predictions,list) or not isinstance(labels,dict):
        raise ValueError("invalid inputs")
    tp=fp=fn=tn=0
    missing=0
    seen=set()
    for p in predictions:
        if not isinstance(p,dict) or not isinstance(p.get("id"),str) or type(p.get("alert")) is not bool:
            raise ValueError("invalid prediction")
        ident=p["id"]
        if ident in seen:raise ValueError("duplicate prediction")
        seen.add(ident)
        prediction_at=_date(p.get("predicted_at_utc"))
        if prediction_at>cutoff:raise ValueError("prediction after evaluation cutoff")
        label=labels.get(ident)
        if label is None:
            missing+=1
            continue
        if not isinstance(label,dict) or type(label.get("positive")) is not bool:
            raise ValueError("invalid independent label")
        adjudicated=_date(label.get("adjudicated_at_utc"))
        if adjudicated>cutoff:raise ValueError("label unavailable at cutoff")
        if adjudicated<=prediction_at:
            raise ValueError("label existed before prediction: potential leakage")
        alert=p["alert"]
        positive=label["positive"]
        if alert and positive:tp+=1
        elif alert:fp+=1
        elif positive:fn+=1
        else:tn+=1
    precision=tp/(tp+fp) if tp+fp else None
    recall=tp/(tp+fn) if tp+fn else None
    return {"version":VERSION,"tp":tp,"fp":fp,"fn":fn,"tn":tn,
            "unlabeled":missing,"precision":precision,"recall":recall,
            "false_discovery_rate":fp/(tp+fp) if tp+fp else None,
            "market_prediction_validated":False,
            "note":"Labels require independent, documented, point-in-time adjudication."}
