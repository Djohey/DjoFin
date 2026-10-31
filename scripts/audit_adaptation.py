"""Rapport de comparaison avant/après adaptation des frais."""
import argparse
import json
from pathlib import Path
from dataclasses import replace
from djofin.snapshots import load_snapshot
from djofin.politiques import Regles, comparer_regle
from djofin.tarification import Tarification

TARIFS = {
    "A — 0,10 %": Tarification(pourcentage=.001),
    "B — 1 € fixe": Tarification(fixe=1, pourcentage=0),
    "C — 1 € + 0,10 %": Tarification(fixe=1, pourcentage=.001),
    "D — 0,50 %, minimum 2 €": Tarification(pourcentage=.005, minimum=2),
}
MODES = ("initial", "progressif", "volatilite", "combine")

def repli_maximal(valeurs):
    sommet = 0
    pire = 0
    for point in valeurs:
        valeur = point["valeur"]
        if valeur is None:
            continue
        sommet = max(sommet, valeur)
        pire = min(pire, valeur / sommet - 1)
    return 100*pire

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", required=True)
    parser.add_argument("--metadata", required=True)
    parser.add_argument("--sortie", required=True)
    a = parser.parse_args()
    meta = json.loads(Path(a.metadata).read_text(encoding="utf-8"))
    snap = load_snapshot(Path(a.csv).read_text(encoding="utf-8"),
        ticker=meta["ticker"], source=meta["source"],
        retrieved_at_utc=meta["retrieved_at_utc"], currency=meta["currency"])
    if snap.csv_sha256 != meta["csv_sha256"]:
        raise ValueError("Archive historique altérée")
    lines = ["# DjoFin — Audit préparatoire des frais et des décisions",
             "", "## Objet et provenance",
             f"- Actif : {snap.ticker} ; période : {snap.bars[0].day} — {snap.bars[-1].day}.",
             f"- Source : {snap.source} ; récupération : {snap.retrieved_at_utc}.",
             f"- Empreinte CSV : `{snap.csv_sha256}`.",
             "- Capital initial : 1 000 € fictifs ; ordres à la prochaine ouverture.",
             "", "## Choix de conception",
             "- Quatre politiques : initiale, progressive, volatilité, combinée.",
             "- Quatre barèmes : proportionnel, fixe, mixte, minimum de perception.",
             "- Règle initiale : refus si frais > 2 % du montant.",
             "- Adaptation : augmenter seulement les petits ordres d'achat progressifs",
             "  lorsque les frais dépassent 2 %, dans la limite de 35 % d'exposition",
             "  initiale ; préserver les sorties réduisant le risque.",
             "- Les paramètres sont hypothétiques, non calibrés sur un échantillon indépendant.",
             "", "## Résultats : avant / après adaptation",
             "| Barème | Politique | Avant (€) | Après (€) | Écart (€) |",
             "|---|---|---:|---:|---:|"]
    details = {}
    for nom, tarif in TARIFS.items():
        details[nom] = {}
        for mode in MODES:
            base = Regles(mode=mode, tarification=tarif)
            avant = comparer_regle(list(snap.bars), base)
            apres = comparer_regle(list(snap.bars), replace(base, adaptation_frais=True))
            details[nom][mode] = {"avant": avant, "apres": apres}
            lines.append(f"| {nom} | {mode} | {avant['capital_final']:.2f} | "
                         f"{apres['capital_final']:.2f} | "
                         f"{apres['capital_final']-avant['capital_final']:+.2f} |")
    lines += ["", "## Références passives obligatoires",
              "| Barème | Achat-conservation (€) | 100 % liquidités (€) |",
              "|---|---:|---:|"]
    for nom, tarif in TARIFS.items():
        premier = snap.bars[0].open
        cout = 1000.0
        from djofin.tarification import montant_achat, frais_ordre
        brut = montant_achat(cout, tarif)
        parts = brut / premier
        capital_bh = (cout - brut - frais_ordre(brut, tarif)) + parts * snap.bars[-1].close
        lines.append(f"| {nom} | {capital_bh:.2f} | 1000.00 |")
    lines += ["", "## Contrôles des frais et des risques",
              "| Barème | Politique | Frais avant | Frais après | Opérations après | Adaptations | Refus après | Repli après |",
              "|---|---|---:|---:|---:|---:|---:|---:|"]
    for nom, modes in details.items():
        for mode, d in modes.items():
            resultat_avant, b = d["avant"], d["apres"]
            lines.append(f"| {nom} | {mode} | {sum(x['frais'] for x in resultat_avant['operations']):.2f} | "
                         f"{sum(x['frais'] for x in b['operations']):.2f} | "
                         f"{len(b['operations'])} | {len(b['adaptations'])} | "
                         f"{len(b['ordres_refuses'])} | {repli_maximal(b['valeurs']):.2f} % |")
    lines += ["", "## Points de vigilance pour audit indépendant",
              "1. Le montant adapté est calculé au cours d'ouverture du lendemain ; vérifier les contraintes d'exécution.",
              "2. Une sortie peut désormais être exécutée malgré des frais élevés : contrôler les montants résiduels.",
              "3. Vérifier la cohérence des expositions après frais et la possibilité d'ordres répétés.",
              "4. Le modèle ne tient pas compte des spreads, taxes, fiscalité, liquidité ni parts entières.",
              "5. Les performances peuvent résulter d'une exposition moindre ou de hasard ; tester hors échantillon.",
              "6. Les barèmes et seuils sont fictifs et ne correspondent pas à un courtier identifié.",
              "7. Le test sur une seule série ne valide pas la généralisation ni l'absence de surajustement.",
              "8. Le moteur reste déterministe, sans IA ; aucune probabilité de gain n'est validée.",
              "", "## Questions adressées à l'auditeur",
              "- Existe-t-il une fuite temporelle, un biais de survie ou une comparaison inéquitable ?",
              "- Les ordres et les frais sont-ils correctement comptabilisés, y compris en cas de refus ?",
              "- Le plafonnement de la position initiale est-il cohérent avec le budget et le risque ?",
              "- Quelles contre-expériences, périodes, actifs et stress tests manquent ?",
              "- Quelles conclusions sont insuffisamment démontrées ?",
              "", "## Décision provisoire",
              "Aucune stratégie n'est approuvée pour investissement réel. Revue indépendante nécessaire.", ""]
    sortie = Path(a.sortie)
    sortie.parent.mkdir(parents=True, exist_ok=True)
    sortie.write_text("\n".join(lines), encoding="utf-8")
    sortie.with_suffix(".json").write_text(json.dumps(
        {"source": meta, "comparaisons": details}, ensure_ascii=False, indent=2), encoding="utf-8")
    print("\n".join(lines))

if __name__ == "__main__":
    main()
