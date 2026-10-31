"""Research priority rules V0: deterministic, reversible, and not investment signals."""
from dataclasses import dataclass
import re

DOMAINS = {
    "finance": ("earnings", "revenue", "merger", "acquisition", "dividend", "profit", "results"),
    "geopolitics": ("sanction", "tariff", "conflict", "trade agreement", "embargo"),
    "technology": ("artificial intelligence", "semiconductor", "chip", "ai adoption", "quantum"),
    "pharma": ("clinical trial", "fda", "vaccine", "drug approval", "phase iii", "phase 3"),
    "macro": ("interest rate", "inflation", "monetary policy", "ecb", "central bank", "forecast"),
}
HIGH_IMPACT = ("unexpected", "emergency", "halt", "withdraw", "recall", "bankruptcy", "approval", "rejection")
VERSION = "research-priority-v0.1"

def matches(text, term):
    return bool(re.search(r"(?<!\w)" + re.escape(term) + r"(?!\w)", text, re.I))

def classify(item):
    title = item.get("title", "")
    domains = sorted(domain for domain, terms in DOMAINS.items() if any(matches(title, term) for term in terms))
    triggers = sorted(term for term in HIGH_IMPACT if matches(title, term))
    unknown = not domains
    # Triage, not impact prediction: uncertain cases are NOT silently discarded.
    priority = "review" if triggers or len(domains) >= 2 else ("explore" if unknown else "routine")
    return {
        "id": item["id"],
        "rule_version": VERSION,
        "domains": domains,
        "priority": priority,
        "unknown_topic": unknown,
        "triggers": triggers,
        "rationale": "keyword triage only; market impact and surprise unverified",
        "investment_signal": False,
        "needs_human_or_research_validation": True,
    }
