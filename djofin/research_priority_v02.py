"""DjoFin research triage candidate v0.2. Keyword triage, never trading advice.
Adapted from external audit supplied by user; retained separately from stable v0.1.
"""
from hashlib import sha256
import json
import re
import unicodedata

VERSION = "research-priority-v0.2"

class TriageError(ValueError):
    """Invalid item."""

DOMAINS = {
    "finance": [
        r"earnings?", r"revenues?", r"profits?", r"dividends?", r"mergers?",
        r"acquisitions?", r"acquir(?:e|es|ed|ing)", r"takeovers?", r"buyouts?",
        r"(?:quarterly|annual|full year|half year) results",
        r"(?:resultats|benefices?|chiffre d affaires) (?:annuels?|trimestriels?|semestriels?)",
        r"resultats (?:de|du|d)", r"benefices?", r"dividendes?",
        r"fusions?", r"rachats?", r"acquisitions?", r"opa",
        r"(?:earnings|revenue|profit|sales) (?:forecast|guidance|outlook)",
        r"guidance", r"profit warning", r"avertissement sur (?:les )?resultats",
    ],
    "geopolitics": [
        r"sanctions?", r"tariffs?", r"embargo(?:es)?", r"trade (?:agreement|deal|war)s?",
        r"(?:armed|military|border) conflicts?", r"war (?:in|with|on|between|against)", r"invasion",
        r"export (?:controls?|bans?)", r"controles? (?:a l|des) exportations?",
        r"droits de douane", r"guerre commerciale", r"accord commercial", r"conflit arme",
    ],
    "technology": [
        r"artificial intelligence", r"intelligence artificielle", r"semiconductors?",
        r"semi conducteurs?", r"(?:computer|memory|ai) chips?", r"chipmakers?",
        r"microprocesseurs?", r"puces? (?:electroniques?|informatiques?)",
        r"quantum (?:computing|computers?)", r"informatique quantique",
    ],
    "pharma": [
        r"clinical trials?", r"drug trials?", r"essais? cliniques?", r"(?:trial|study) (?:results|data)",
        r"vaccines?", r"vaccins?", r"drug approvals?", r"phase (?:iii|3|ii|2)",
        r"marketing authori[sz]ation", r"autorisation de mise sur le marche",
    ],
    "macro": [
        r"interest rates?", r"taux (?:directeurs?|d interet)", r"inflation", r"deflation",
        r"monetary policy", r"politique monetaire", r"central banks?", r"banques? centrales?",
        r"rate (?:hikes?|cuts?)", r"hausse des taux", r"baisse des taux",
        r"(?:gdp|growth|inflation|economic) forecasts?", r"previsions? (?:de croissance|economiques?)",
        r"recession", r"pib",
    ],
}
ACRONYMS = {
    "technology": [r"AI", r"IA"],
    "pharma": [r"FDA", r"EMA"],
    "macro": [r"ECB", r"BCE", r"FED", r"Fed", r"Federal Reserve", r"Reserve federale"],
    "finance": [r"IPO", r"M&A"],
}
TRIGGERS = [
    r"unexpected(?:ly)?", r"surprise", r"inattendu(?:e|s|es)?", r"emergency", r"urgence",
    r"halt(?:s|ed)?", r"suspend(?:s|ed)?|suspension", r"withdr(?:aw|aws|awn|ew|awal)",
    r"retir(?:e|ee|es|ees)", r"recalls?|recalled", r"rappels?", r"bankruptcy|bankrupt",
    r"faillite", r"chapter 11", r"rejections?|rejected|rejects", r"rejet(?:e|ee)?",
    r"approvals?|approved|approves", r"approbation|approuve(?:e)?", r"profit warning",
]
EXCLUSIONS = [
    r"blue chips?", r"conflicts? of interest", r"conflits? d interets?",
    r"weather forecasts?", r"previsions? meteo", r"board approval", r"shareholder approval",
    r"approbation des comptes",
]
NEGATIONS = r"(?:no|not|without|aucune?|pas d|pas de|sans|ni)"
PRIORITIES = ("review", "explore", "routine")

def _strip_accents(text):
    return "".join(c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c))

def normalise(text):
    text = _strip_accents(text).lower()
    text = re.sub(r"[\-‐‑–—_/’'`]", " ", text)
    return re.sub(r"\s+", " ", text).strip()

def _compile(pattern, flags=0):
    return re.compile(r"(?<!\w)(?:" + pattern + r")(?!\w)", flags)

_DOMAIN_RX = {d: [(p, _compile(p)) for p in ps] for d, ps in DOMAINS.items()}
_ACRONYM_RX = {d: [(p, _compile(p)) for p in ps] for d, ps in ACRONYMS.items()}
_TRIGGER_RX = [(p, _compile(p)) for p in TRIGGERS]
_EXCLUSION_RX = [_compile(p) for p in EXCLUSIONS]
_NEGATED = re.compile(r"(?<!\w)" + NEGATIONS + r"(?:\s+\w+){0,2}\s+$")
RULES_SHA256 = sha256(json.dumps(
    {"v": VERSION, "d": DOMAINS, "a": ACRONYMS, "t": TRIGGERS, "e": EXCLUSIONS, "n": NEGATIONS},
    sort_keys=True).encode()).hexdigest()

def _mask_exclusions(text):
    for rx in _EXCLUSION_RX:
        text = rx.sub(lambda m: " " * len(m.group(0)), text)
    return text

def classify(item):
    if not isinstance(item, dict):
        raise TriageError("Item must be a dict")
    ident = item.get("id")
    if not isinstance(ident, str) or not ident.strip():
        raise TriageError("Item id must be a non-empty string")
    parts = []
    for key in ("title", "summary"):
        value = item.get(key)
        if value is None:
            continue
        if not isinstance(value, str):
            raise TriageError(f"{key} must be text")
        parts.append(value)
    raw = " . ".join(parts)
    text = _mask_exclusions(normalise(raw))
    raw_acr = _mask_exclusions(_strip_accents(raw))
    matched = {}
    for domain, rules in _DOMAIN_RX.items():
        hits = sorted({m.group(0) for _, rx in rules for m in rx.finditer(text)})
        hits += sorted({m.group(0) for _, rx in _ACRONYM_RX.get(domain, []) for m in rx.finditer(raw_acr)})
        if hits:
            matched[domain] = hits
    triggers, negated = [], []
    for _, rx in _TRIGGER_RX:
        for m in rx.finditer(text):
            (negated if _NEGATED.search(text[:m.start()]) else triggers).append(m.group(0))
    triggers, negated = sorted(set(triggers)), sorted(set(negated))
    domains = sorted(matched)
    unknown = not domains and not triggers
    if triggers or len(domains) >= 2:
        priority = "review"
    elif unknown or negated:
        priority = "explore"
    else:
        priority = "routine"
    return {
        "id": ident, "rule_version": VERSION, "rules_sha256": RULES_SHA256,
        "domains": domains, "matched_terms": matched, "priority": priority,
        "unknown_topic": unknown, "triggers": triggers, "negated_triggers": negated,
        "empty_text": not raw.strip(),
        "rationale": "keyword triage only; market impact and surprise unverified",
        "investment_signal": False, "needs_human_or_research_validation": True,
    }
