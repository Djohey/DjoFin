"""Research decision gate: economics-inspired, not a market predictor.

Bayesian updates require independently calibrated likelihood ratios.
No headline may create evidence, probability or a trade.
"""
import math
from djofin.news_triage import triage_entry
from djofin.evidence_ledger import review

VERSION = "research-gate-v0.1"
WEIGHTS = {"impact": 0.30, "novelty": 0.25, "uncertainty": 0.20,
           "verifiability": 0.15, "cross_domain": 0.10}
MIN_SCORE = 0.60

def bayes_update(prior, likelihood_ratios):
    """Odds form of Bayes' rule, only for independently calibrated evidence.

    Repeated or correlated evidence MUST NOT be entered as independent ratios.
    """
    if not isinstance(prior, (int, float)) or isinstance(prior, bool) or not math.isfinite(prior) or not 0 < prior < 1:
        raise ValueError("prior must be strictly between 0 and 1")
    if not isinstance(likelihood_ratios, (list, tuple)):
        raise ValueError("ratios must be a sequence")
    if not likelihood_ratios:
        return float(prior)
    if len(likelihood_ratios) > 20:
        raise ValueError("too many updates")
    log_odds = math.log(prior / (1-prior))
    for ratio in likelihood_ratios:
        if isinstance(ratio, bool) or not isinstance(ratio, (float, int)) or not math.isfinite(ratio) or ratio <= 0:
            raise ValueError("ratios must be finite and positive")
        log_odds += math.log(ratio)
    return 1 / (1 + math.exp(-log_odds)) if log_odds >= 0 else math.exp(log_odds) / (1 + math.exp(log_odds))

def rank_research(entry, assessment=None, *, ledger=None):
    """Prioritize investigation, not buying or selling.

    Assessment is explicitly a human research estimate (0..1), not inferred
    from the headline. Missing estimates produce an unscored candidate.
    """
    candidate = triage_entry(entry)
    result = {"version": VERSION, "news_id": candidate["id"],
              "topic": candidate["topic"], "category": candidate["category"],
              "eligible_as_evidence": False, "investment_signal": False,
              "bayesian_probability": None, "decision": "collect_more_information",
              "score": None, "score_kind": "unvalidated_research_heuristic",
              "unknowns": list(candidate["unknowns"])}
    if ledger is not None:
        verdict = review(ledger)
        result["ledger_digest"] = verdict["ledger_digest"]
        result["contradictory_evidence_present"] = verdict["has_contradiction"]
        result["unknowns"].extend(verdict["unknowns"])
    if assessment is None:
        result["unknowns"].append("no independent assessment of research dimensions")
        return result
    if not isinstance(assessment, dict) or set(assessment) != set(WEIGHTS):
        raise ValueError("assessment must supply exactly five dimensions")
    for key, value in assessment.items():
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 <= value <= 1:
            raise ValueError("assessment dimensions must be finite in [0,1]")
    score = sum(WEIGHTS[key] * assessment[key] for key in WEIGHTS)
    result["score"] = round(score, 4)
    result["decision"] = "investigate" if score >= MIN_SCORE else "defer"
    result["unknowns"].append("score is a subjective ranking, not calibrated to returns")
    return result
