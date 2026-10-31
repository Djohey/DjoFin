"""Seize scénarios de coûts et quatre stratégies, sur une même archive."""
import argparse
import json
from pathlib import Path
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

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--csv", required=True)
    p.add_argument("--metadata", required=True)
    p.add_argument("--sortie", required=True)
    a = p.parse_args()
    meta = json.loads(Path(a.metadata).read_text(encoding="utf-8"))
    snapshot = load_snapshot(Path(a.csv).read_text(encoding="utf-8"),
                             ticker=meta["ticker"], source=meta["source"],
                             retrieved_at_utc=meta["retrieved_at_utc"],
                             currency=meta["currency"])
    if snapshot.csv_sha256 != meta["csv_sha256"]:
        raise ValueError("Empreinte du fichier modifiée")
    lignes = ["# DjoFin — Comparaison des commissions et stratégies", "",
              f"Instrument : {snapshot.ticker} ; période : {snapshot.bars[0].day} au {snapshot.bars[-1].day}.",
              f"SHA-256 : `{snapshot.csv_sha256}`.", "",
              "| Barème | Stratégie | Capital final | Rendement | Ordres | Frais | Refus |",
              "|---|---|---:|---:|---:|---:|---:|"]
    detail = {}
    for libelle, tarif in TARIFS.items():
        detail[libelle] = {}
        for mode in MODES:
            r = comparer_regle(list(snapshot.bars), Regles(mode=mode, tarification=tarif))
            detail[libelle][mode] = r
            frais = sum(t["frais"] for t in r["operations"])
            lignes.append(f"| {libelle} | {mode} | {r['capital_final']:.2f} € | "
                          f"{(r['capital_final']/1000-1)*100:.2f} % | "
                          f"{len(r['operations'])} | {frais:.2f} € | "
                          f"{len(r['ordres_refuses'])} |")
    lignes += ["", "## Précautions",
              "- Comparaison rétrospective exploratoire, pas de validation hors échantillon.",
              "- Seuil de refus : frais supérieurs à 2 % du montant brut.",
              "- Frais estimés à l'exécution, à l'ouverture suivante.",
              "- Le coût d'opportunité des ordres refusés n'est pas isolé.",
              "- Parts fractionnées fictives ; spreads, fiscalité et liquidité non modélisés.",
              "- Une stratégie moins exposée peut sembler moins risquée sans meilleur signal.",
              ""]
    sortie = Path(a.sortie)
    sortie.parent.mkdir(parents=True, exist_ok=True)
    sortie.write_text("\n".join(lignes), encoding="utf-8")
    sortie.with_suffix(".json").write_text(
        json.dumps({"metadata": meta, "scenarios": detail}, ensure_ascii=False, indent=2),
        encoding="utf-8")
    print("\n".join(lignes))

if __name__ == "__main__":
    main()
