"""Outils quantitatifs P0 : dimensionnement, volatilité et scénarios.

Aucune prévision automatique de rendement ; les hypothèses doivent être
fournies explicitement. Unités : rendements décimaux, pas pourcentages.
"""
from dataclasses import dataclass, asdict
from hashlib import sha256
import json
import math
import random


def _probabilite(x):
    return math.isfinite(x) and 0 <= x <= 1


def fraction_kelly(probabilite_gain: float, gain_net: float,
                   perte_nette: float, prudence: float = 0.25,
                   plafond: float = 0.20) -> dict:
    """Kelly binaire : gain_net et perte_nette sont les gains/pertes par euro
    exposé. Formule inapplicable sans probabilités estimées de façon crédible.
    """
    if not _probabilite(probabilite_gain):
        raise ValueError("Probabilité invalide")
    if not all(math.isfinite(x) and x > 0 for x in (gain_net, perte_nette)):
        raise ValueError("Gains et pertes doivent être strictement positifs")
    if not _probabilite(prudence) or not _probabilite(plafond):
        raise ValueError("Prudence et plafond doivent être entre 0 et 1")
    brut = (probabilite_gain * gain_net -
            (1 - probabilite_gain) * perte_nette) / (gain_net * perte_nette)
    return {"kelly_theorique": brut, "fraction_retenue": min(plafond, max(0, brut * prudence)),
            "avertissement": "Hypothèses fournies, non estimées ni validées par DjoFin."}


def volatilite_historique(rendements: list[float], periodes_par_an: int = 252) -> dict:
    """Écart-type empirique annualisé ; aucune prévision GARCH ici."""
    if len(rendements) < 2 or periodes_par_an <= 0:
        raise ValueError("Au moins deux rendements et une fréquence positive")
    if any(not math.isfinite(r) or r <= -1 for r in rendements):
        raise ValueError("Rendements non finis ou inférieurs ou égaux à -100 %")
    moyenne = sum(rendements) / len(rendements)
    variance = sum((x - moyenne) ** 2 for x in rendements) / (len(rendements) - 1)
    return {"volatilite_annualisee": math.sqrt(variance * periodes_par_an),
            "nombre_observations": len(rendements), "methode": "ecart_type_empirique"}


@dataclass(frozen=True)
class HypothesesMonteCarlo:
    capital: float = 1000.0
    rendement_moyen_journalier: float = 0.0
    volatilite_journaliere: float = 0.01
    jours: int = 252
    simulations: int = 1000
    graine: int = 42

    def __post_init__(self):
        if not all(math.isfinite(x) for x in (self.capital, self.rendement_moyen_journalier,
                                              self.volatilite_journaliere)):
            raise ValueError("Hypothèses non finies")
        if self.capital <= 0 or self.volatilite_journaliere < 0:
            raise ValueError("Capital ou volatilité invalide")
        if not (1 <= self.jours <= 10000 and 2 <= self.simulations <= 100000):
            raise ValueError("Nombre de jours/simulations invalide")


def monte_carlo(h: HypothesesMonteCarlo) -> dict:
    """Simulation lognormale illustrative ; ne prédit pas les crises extrêmes.

    Chaque tirage représente un rendement logarithmique journalier. La graine
    garantit la reproductibilité, pas la justesse du modèle.
    """
    alea = random.Random(h.graine)
    capitaux, pertes_max = [], []
    for _ in range(h.simulations):
        capital = h.capital
        sommet = capital
        drawdown = 0.0
        for _ in range(h.jours):
            capital *= math.exp(alea.gauss(h.rendement_moyen_journalier,
                                          h.volatilite_journaliere))
            sommet = max(sommet, capital)
            drawdown = min(drawdown, capital / sommet - 1)
        capitaux.append(capital)
        pertes_max.append(drawdown)
    capitaux.sort()
    pertes_max.sort()
    n = len(capitaux)
    resultat = {
        "hypotheses": asdict(h),
        "capital_median": capitaux[n // 2],
        "capital_percentile_5": capitaux[int((n - 1) * 0.05)],
        "capital_percentile_95": capitaux[int((n - 1) * 0.95)],
        "probabilite_perte_empirique": sum(v < h.capital for v in capitaux) / n,
        "drawdown_median": pertes_max[n // 2],
        "avertissements": [
            "Distribution lognormale hypothétique : queues épaisses et crises non modélisées.",
            "Les paramètres sont fournis et non prédits.",
            "Résultats simulés, pas des probabilités de marché garanties.",
        ],
    }
    resultat["empreinte_sha256"] = sha256(json.dumps(
        resultat, sort_keys=True, allow_nan=False).encode()).hexdigest()
    return resultat
