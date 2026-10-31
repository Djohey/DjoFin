"""Tests de stratégies progressives, sans données futures."""
from dataclasses import dataclass
from .simulator import Bar
import math
from .tarification import Tarification, frais_ordre, montant_achat

@dataclass(frozen=True)
class Regles:
    mode: str = "progressif"
    rapide: int = 20
    lente: int = 50
    frais: float = .001
    capital: float = 1000
    seuil: float = .01
    confirmation: int = 3
    attente: int = 10
    objectif_vol: float = .15
    tarification: Tarification | None = None
    seuil_frais_relatifs: float = .02
    adaptation_frais: bool = False
    exposition_initiale_max: float = .35

def comparer_regle(bars: list[Bar], r: Regles) -> dict:
    if r.mode not in ("initial", "progressif", "volatilite", "combine"):
        raise ValueError("Mode inconnu")
    if not 1 <= r.rapide < r.lente or r.capital <= 0:
        raise ValueError("Paramètres invalides")
    if not 0 <= r.frais < 1 or not 0 <= r.seuil < 1:
        raise ValueError("Paramètres invalides")
    if r.confirmation < 1 or r.attente < 0 or r.objectif_vol <= 0:
        raise ValueError("Paramètres invalides")
    if not 0 <= r.seuil_frais_relatifs <= 1:
        raise ValueError("Seuil de frais invalide")
    if not 0 < r.exposition_initiale_max <= 1:
        raise ValueError("Plafond d exposition invalide")
    if not bars or [b.day for b in bars] != sorted(set(b.day for b in bars)):
        raise ValueError("Dates invalides")
    liquidites, parts = r.capital, 0.
    historique, operations, decisions, valeurs = [], [], [], []
    ordre = None
    suite = 0
    dernier = -100000
    refuses = []
    adaptations = []
    dernier_refus = None
    for i, b in enumerate(bars):
        if ordre is not None and b.open is not None:
            cible, date_signal = ordre
            valeur = liquidites + parts * b.open
            variation = cible * valeur - parts * b.open
            tarif = r.tarification or Tarification(pourcentage=r.frais)
            if variation > 0.01:
                brut = montant_achat(min(variation, liquidites), tarif)
                if (r.adaptation_frais and r.mode in ("progressif", "combine")
                        and brut > .01 and frais_ordre(brut, tarif) / brut > r.seuil_frais_relatifs):
                    exposition = parts*b.open/valeur
                    plafond = r.exposition_initiale_max if parts <= 1e-12 else min(1., exposition + .35)
                    budget_max = min(liquidites, max(0., plafond*valeur-parts*b.open))
                    maximum = montant_achat(budget_max, tarif)
                    if maximum > brut and frais_ordre(maximum, tarif)/maximum <= r.seuil_frais_relatifs:
                        bas, haut = brut, maximum
                        for _ in range(40):
                            milieu = (bas+haut)/2
                            if frais_ordre(milieu, tarif)/milieu <= r.seuil_frais_relatifs:
                                haut = milieu
                            else:
                                bas = milieu
                        adaptations.append({"date": b.day, "signal": date_signal,
                                            "montant_initial": brut,
                                            "montant_adapte": haut,
                                            "motif": "Commission trop elevee pour ordre initial"})
                        brut = haut
                if brut > .01 and frais_ordre(brut, tarif) / brut <= r.seuil_frais_relatifs:
                    cout = frais_ordre(brut, tarif)
                    liquidites -= brut + cout
                    parts += brut / b.open
                    operations.append({"date": b.day, "signal": date_signal,
                                       "sens": "achat", "frais": cout})
                    dernier = i
                    dernier_refus = None
                elif brut > .01:
                    if not r.adaptation_frais or dernier_refus != "achat":
                        refuses.append({"date": b.day, "motif": "frais disproportionnes", "montant": brut})
                    dernier_refus = "achat"
            elif variation < -.01:
                brut = min(-variation, parts * b.open)
                if brut > .01 and (frais_ordre(brut, tarif) / brut <= r.seuil_frais_relatifs
                                   or (r.adaptation_frais and brut > frais_ordre(brut, tarif))):
                    cout = frais_ordre(brut, tarif)
                    liquidites += brut - cout
                    parts = 0.0 if cible == 0 else parts - brut / b.open
                    operations.append({"date": b.day, "signal": date_signal,
                                       "sens": "vente", "frais": cout})
                    dernier = i
                elif brut > .01:
                    refuses.append({"date": b.day, "motif": "frais disproportionnes", "montant": brut})
        ordre = None
        historique.append(b.close)
        decision, justification = "attente", "Historique insuffisant"
        if len(historique) >= r.lente and all(x is not None for x in historique[-r.lente:]):
            courte = math.fsum(historique[-r.rapide:]) / r.rapide
            longue = math.fsum(historique[-r.lente:]) / r.lente
            ecart = courte / longue - 1
            bande = 0 if r.mode in ("initial", "volatilite") else r.seuil
            suite = suite + 1 if ecart > bande and suite >= 0 else (
                suite - 1 if ecart < -bande and suite <= 0 else (
                1 if ecart > bande else -1 if ecart < -bande else 0))
            requis = 1 if r.mode in ("initial", "volatilite") else r.confirmation
            exposition = parts * b.close / (liquidites + parts * b.close)
            cible = None
            if suite >= requis:
                cible = 1. if r.mode in ("initial", "volatilite") else min(
                    1., .10 if parts == 0 else exposition + .20)
            elif suite <= -requis:
                cible = 0.
                dernier_refus = None
            if cible is not None and r.mode in ("volatilite", "combine"):
                fenetre = historique[-21:]
                ret = [math.log(fenetre[j] / fenetre[j-1]) for j in range(1,len(fenetre))]
                if len(ret) > 1:
                    moyenne = sum(ret) / len(ret)
                    sigma = math.sqrt(sum((x-moyenne)**2 for x in ret)/(len(ret)-1)*252)
                    if sigma > 0:
                        cible = min(cible, r.objectif_vol / sigma)
            if cible is not None and abs(cible - exposition) >= .02 and (
                i - dernier >= (0 if r.mode == "initial" else r.attente)):
                ordre = (cible, b.day)
                decision = "achat" if cible > exposition else "vente"
                justification = f"Écart des moyennes : {ecart:.5f}; cible : {cible:.3f}"
            else:
                justification = "Signal non confirmé ou transaction évitée"
        decisions.append({"date": b.day, "decision": decision,
                          "justification": justification,
                          "information_disponible": b.day + " clôture"})
        valeurs.append({"date": b.day, "valeur": liquidites + parts*b.close
                        if b.close is not None else None})
    return {"mode": r.mode, "operations": operations, "ordres_refuses": refuses, "adaptations": adaptations, "decisions": decisions,
            "valeurs": valeurs, "capital_final": valeurs[-1]["valeur"]}
