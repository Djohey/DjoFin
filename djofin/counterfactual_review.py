"""Counterfactual decision review: includes actions, abstentions and unseen events.

A retrospective outcome does not prove predictability. All opportunities require
a pre-outcome universe snapshot, decision record, and separately dated outcome.
No real orders, recommendation, automatic retraining or invented market data.
"""
from datetime import datetime, timezone
import math

VERSION="counterfactual-review-v0.1"
ACTIONS={"invest","abstain","not_detected"}
OUTCOMES={"gain","loss","flat"}
REASONS={"risk","insufficient_evidence","low_priority","not_in_universe",
         "not_collected","filtered","capacity","other"}

def _time(value):
    if not isinstance(value,str):raise ValueError("timestamp required")
    try:t=datetime.fromisoformat(value.replace("Z","+00:00"))
    except ValueError as e:raise ValueError("invalid timestamp") from e
    if t.tzinfo is None or t.utcoffset() is None:raise ValueError("timezone required")
    return t.astimezone(timezone.utc)

def review_decisions(records,*,cutoff_utc):
    """Evaluate documented decisions without converting hindsight into foresight.

    Fields: id, observed_at_utc, decision_at_utc, outcome_at_utc, action,
    outcome, reason, in_universe_at_decision, predecision_snapshot_sha256,
    outcome_source_sha256. 'not_detected' means independent universe coverage
    was recorded at decision time; it must not be inferred from later winners.
    """
    if not isinstance(records,list) or len(records)>10000:
        raise ValueError("invalid records")
    cutoff=_time(cutoff_utc)
    seen=set()
    matrix={a:{o:0 for o in sorted(OUTCOMES)} for a in sorted(ACTIONS)}
    uncertain=[]
    for record in records:
        if not isinstance(record,dict):raise ValueError("invalid record")
        ident=record.get("id")
        if not isinstance(ident,str) or not ident.strip() or ident in seen:
            raise ValueError("missing or duplicate id")
        seen.add(ident)
        action,outcome,reason=(record.get(k) for k in ("action","outcome","reason"))
        if action not in ACTIONS or outcome not in OUTCOMES or reason not in REASONS:
            raise ValueError("invalid action, outcome or reason")
        if type(record.get("in_universe_at_decision")) is not bool:
            raise ValueError("universe flag required")
        for key in ("predecision_snapshot_sha256","outcome_source_sha256"):
            value=record.get(key)
            if not isinstance(value,str) or len(value)!=64 or any(c not in "0123456789abcdef" for c in value):
                raise ValueError("documented content hash required")
        observed=_time(record.get("observed_at_utc"))
        decided=_time(record.get("decision_at_utc"))
        outcome_time=_time(record.get("outcome_at_utc"))
        if observed>decided or decided>=outcome_time or outcome_time>cutoff:
            raise ValueError("temporal leakage or unavailable outcome")
        if action=="not_detected":
            if not record["in_universe_at_decision"] or reason not in {"not_collected","filtered","capacity"}:
                raise ValueError("missed detection requires frozen prior universe and reason")
        elif not record["in_universe_at_decision"]:
            raise ValueError("decision outside frozen universe")
        matrix[action][outcome]+=1
        if action=="not_detected":
            uncertain.append({"id":ident,"finding":"coverage_gap_not_proof_of_predictability"})
        elif action=="abstain" and outcome=="gain":
            uncertain.append({"id":ident,"finding":"missed_gain_not_necessarily_error"})
        elif action=="invest" and outcome=="gain":
            uncertain.append({"id":ident,"finding":"profit_not_proof_of_skill"})
        elif action=="abstain" and outcome=="loss":
            uncertain.append({"id":ident,"finding":"avoided_loss_not_proof_of_skill"})
    return {"version":VERSION,"total":len(records),"matrix":matrix,
            "review_flags":uncertain,"investment_signal":False,
            "automatic_learning_permitted":False,
            "limitations":["Outcome categories require independent predeclared horizon and benchmark",
                           "No unobserved assets can be counted without frozen universe coverage",
                           "No causal attribution or hindsight-free predictability demonstrated",
                           "Selection bias, survivorship bias and opportunity costs remain unmeasured"]}
