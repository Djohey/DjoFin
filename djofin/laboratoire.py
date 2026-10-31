"""Laboratoire de réévaluation P0 : comparer des règles sans réécrire le passé.

Ce module teste des règles mathématiques déterministes. Il ne constitue pas
encore une intelligence artificielle apprenante ni une preuve d'absence de
connaissances historiques dans un modèle de langage.
"""
from dataclasses import dataclass, asdict
from hashlib import sha256
import json
from .simulator import Bar, Config, simulate


@dataclass(frozen=True)
class Apprentissage:
    identifiant: str
    hypothese: str
    justification: str
    source: str
    date_publication: str
    date_integration: str
    limites: str

    def __post_init__(self):
        from datetime import date
        date.fromisoformat(self.date_publication)
        date.fromisoformat(self.date_integration)
        if self.date_publication > self.date_integration:
            raise ValueError("Une étude ne peut être intégrée avant publication")
        if not all((self.identifiant, self.hypothese, self.justification,
                    self.source, self.limites)):
            raise ValueError("Les justifications et sources sont obligatoires")


def _empreinte(obj):
    return sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False,
                             allow_nan=False).encode("utf-8")).hexdigest()


def rejouer(bars: list[Bar], initiale: Config, candidate: Config,
            apprentissage: Apprentissage, debut_validation: str) -> dict:
    """Compare les mêmes données ; la date de validation doit être postérieure
    à une période d'exploration non vide. Aucune optimisation n'est effectuée.

    Les métriques de validation sont calculées en partant du capital initial
    de chaque stratégie à la dernière clôture *avant* la validation.
    """
    from datetime import date
    date.fromisoformat(debut_validation)
    if not bars or bars[0].day >= debut_validation or bars[-1].day < debut_validation:
        raise ValueError("Périodes d'exploration et de validation requises")
    if initiale.initial_cash != candidate.initial_cash:
        raise ValueError("Même capital initial obligatoire")
    a = simulate(bars, initiale)
    b = simulate(bars, candidate)
    avant = [i for i, bar in enumerate(bars) if bar.day < debut_validation]
    apres = [i for i, bar in enumerate(bars) if bar.day >= debut_validation]
    def valeur(result, index):
        return result["equity"][index]["value"]
    def stats(result):
        debut = valeur(result, avant[-1])
        fin = valeur(result, apres[-1])
        if debut is None or fin is None or debut <= 0:
            raise ValueError("Clôtures valides requises aux bornes de validation")
        trades = [t for t in result["trades"] if t["date"] >= debut_validation]
        return {"capital_debut_validation": debut, "capital_fin_validation": fin,
                "rendement_validation_pct": 100 * (fin / debut - 1),
                "nombre_operations_validation": len(trades),
                "frais_validation": sum(t["fee"] for t in trades)}
    sa, sb = stats(a), stats(b)
    # Chaque décision est accompagnée de ses indicateurs et de sa date limite
    # d'information, fournis par le moteur de simulation.
    differences = [
        {"date": da["date"], "decision_initiale": da["action"],
         "decision_candidate": db["action"],
         "informations_disponibles_jusqua": da["information_cutoff"],
         "justification_initiale": {"moyenne_rapide": da.get("fast_ma"),
                                    "moyenne_lente": da.get("slow_ma")},
         "justification_candidate": {"moyenne_rapide": db.get("fast_ma"),
                                     "moyenne_lente": db.get("slow_ma")}}
        for da, db in zip(a["decisions"], b["decisions"])
        if da["action"] != db["action"]
    ]
    dossier = {
        "apprentissage": asdict(apprentissage),
        "parametres_initiaux": asdict(initiale),
        "parametres_candidats": asdict(candidate),
        "debut_validation": debut_validation,
        "empreinte_donnees": a["manifest"]["input_sha256"],
        "resultat_initial": sa, "resultat_candidat": sb,
        "ecart_rendement_points": sb["rendement_validation_pct"] - sa["rendement_validation_pct"],
        "differences_decisions": differences,
        "limites": [
            "Comparaison rétrospective : ne prouve pas une capacité prédictive.",
            "Les décisions de la validation héritent des positions de l'exploration.",
            "Les deux règles sont évaluées sur le même marché, pas sur des périodes indépendantes.",
            "La sélection des paramètres doit être figée avant l'analyse de validation.",
            "Une variation de rendement ne prouve pas que le raisonnement est meilleur.",
        ],
    }
    dossier["empreinte_dossier"] = _empreinte(dossier)
    return dossier
