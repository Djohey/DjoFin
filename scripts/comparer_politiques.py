"""Comparaison reproductible des quatre politiques sur une archive CSV."""
import argparse
import json
from pathlib import Path
from djofin.snapshots import load_snapshot
from djofin.politiques import Regles, comparer_regle

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--csv", required=True)
    p.add_argument("--metadata", required=True)
    p.add_argument("--sortie", required=True)
    args = p.parse_args()
    meta = json.loads(Path(args.metadata).read_text(encoding="utf-8"))
    s = load_snapshot(Path(args.csv).read_text(encoding="utf-8"),
                      ticker=meta["ticker"], source=meta["source"],
                      retrieved_at_utc=meta["retrieved_at_utc"],
                      currency=meta["currency"])
    if s.csv_sha256 != meta["csv_sha256"]:
        raise ValueError("Archive modifiée")
    resultats = {}
    for mode in ("initial", "progressif", "volatilite", "combine"):
        resultats[mode] = comparer_regle(list(s.bars), Regles(mode=mode))
    lignes = ["# DjoFin — Comparaison de quatre politiques", "",
              f"Instrument : {s.ticker} ; séances : {len(s.bars)}.",
              f"Archive SHA-256 : `{s.csv_sha256}`.", "",
              "| Politique | Capital final | Rendement | Opérations | Frais |",
              "|---|---:|---:|---:|---:|"]
    for nom, r in resultats.items():
        fin = r["capital_final"]
        frais = sum(o["frais"] for o in r["operations"])
        lignes.append(f"| {nom} | {fin:.2f} € | {(fin/1000-1)*100:.2f} % | "
                      f"{len(r['operations'])} | {frais:.2f} € |")
    lignes += ["", "## Limites",
               "- Paramètres définis à titre exploratoire, sans optimisation préalable.",
               "- Comparaison rétrospective sur un seul actif et une seule période.",
               "- La stratégie initiale de ce rapport est une réimplémentation : "
               "les résultats doivent être rapprochés du moteur P0 historique.",
               "- Les frais ne comprennent ni fiscalité ni écart achat/vente.",
               "- Le calcul de volatilité est historique et ne prédit pas les crises.",
               "- La première entrée dépend de la disponibilité des moyennes mobiles.",
               "- Les décisions et transactions sont enregistrées dans le JSON.",
               ""]
    destination = Path(args.sortie)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text("\n".join(lignes), encoding="utf-8")
    destination.with_suffix(".json").write_text(
        json.dumps({"archive": meta, "resultats": resultats},
                   ensure_ascii=False, indent=2), encoding="utf-8")
    print(destination)

if __name__ == "__main__":
    main()
