"""Rapport de simulation P0, à partir d'une archive CSV figée."""
import argparse
import json
from pathlib import Path

from djofin.snapshots import load_snapshot, run_comparison
from djofin.simulator import Config


def drawdown(points):
    peak = None
    worst = 0.0
    for p in points:
        value = p["value"]
        if value is None:
            continue
        peak = value if peak is None else max(peak, value)
        if peak > 0:
            worst = min(worst, value / peak - 1)
    return 100 * worst


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", required=True)
    parser.add_argument("--metadata", required=True)
    parser.add_argument("--sortie", required=True)
    args = parser.parse_args()
    meta = json.loads(Path(args.metadata).read_text(encoding="utf-8"))
    csv_text = Path(args.csv).read_text(encoding="utf-8")
    snapshot = load_snapshot(csv_text, ticker=meta["ticker"],
                             source=meta["source"],
                             retrieved_at_utc=meta["retrieved_at_utc"],
                             currency=meta["currency"])
    if snapshot.csv_sha256 != meta["csv_sha256"]:
        raise ValueError("Empreinte du fichier différente : simulation annulée")
    config = Config(initial_cash=1000, fast_window=20, slow_window=50,
                    fee_bps=10, fixed_fee=0)
    result = run_comparison(snapshot, config)
    strategy = result["strategy"]
    comp = result["comparison"]
    last = next(b.close for b in reversed(snapshot.bars) if b.close is not None)
    first = next(b for b in snapshot.bars if b.open is not None)
    bh_qty = (config.initial_cash / (1 + config.fee_bps / 10000)) / first.open
    bh_fee = config.initial_cash - bh_qty * first.open
    bh_equity = []
    for b in snapshot.bars:
        bh_equity.append({"date": b.day,
                          "value": (bh_qty * b.close if b.close is not None else None)})
    fmt = lambda x: f"{x:,.2f}".replace(",", " ").replace(".", ",")
    lines = [
        "# DjoFin — Premier rapport de simulation historique",
        "",
        "## Périmètre et traçabilité",
        f"- Instrument : {snapshot.ticker} (cotation en {snapshot.currency}, identification du fonds à confirmer).",
        f"- Période : du {snapshot.bars[0].day} au {snapshot.bars[-1].day}.",
        f"- Nombre de séances : {len(snapshot.bars)}.",
        f"- Fournisseur : {snapshot.source}.",
        f"- Données récupérées le : {snapshot.retrieved_at_utc}.",
        f"- Empreinte SHA-256 du CSV : \`{snapshot.csv_sha256}\`.",
        "",
        "## Hypothèses communes",
        "- Capital fictif initial : 1 000 €.",
        "- Frais : 0,10 % par ordre, sans frais fixes.",
        "- Unités fractionnées fictives ; aucune transaction réelle.",
        "- Pas de fiscalité, d'intérêts sur liquidités ni de glissement de prix.",
        "- Prix bruts non ajustés : résultats incomplets si distributions ou opérations sur titres.",
        "",
        "## Stratégies",
        "- **Conservation :** achat à la première ouverture disponible, puis conservation.",
        "- **DjoFin P0 :** moyennes mobiles sur 20 et 50 clôtures ; décision à la clôture, exécution à l'ouverture suivante.",
        "- La stratégie P0 est une règle mathématique fixe, pas une IA apprenante.",
        "",
        "## Résultats",
        "| Indicateur | Conservation | DjoFin P0 |",
        "|---|---:|---:|",
        f"| Capital final | {fmt(comp['buy_hold_ending_value'])} € | {fmt(comp['strategy_ending_value'])} € |",
        f"| Rendement total | {fmt(comp['buy_hold_return_pct'])} % | {fmt(comp['strategy_return_pct'])} % |",
        f"| Repli maximal indicatif | {fmt(drawdown(bh_equity))} % | {fmt(drawdown(strategy['equity']))} % |",
        f"| Nombre d'ordres exécutés | 1 | {len(strategy['trades'])} |",
        f"| Frais d'exécution cumulés | {fmt(bh_fee)} € | {fmt(sum(t['fee'] for t in strategy['trades']))} € |",
        "",
        "## Interprétation et limites",
        "- **Aucune conclusion de supériorité** ne peut être tirée d'une seule période.",
        "- Les moyennes mobiles sont calculées sur des données historiques actuelles, pas des archives de publications datées.",
        "- L'intelligence d'un futur modèle peut connaître le passé : ce test ne valide pas l'absence de fuite de connaissances de l'IA.",
        "- Le repli maximal est calculé sur les valorisations de clôture disponibles et ne reflète pas nécessairement les variations intrajournalières.",
        "- Les prix bruts ne prennent pas en compte les distributions ni les opérations sur titres ; vérifier le caractère capitalisant de l'ETF.",
        "- Le benchmark achète dès la première séance, tandis que P0 attend 50 clôtures : comparaison utile mais exposition initiale différente.",
        "",
        "## Premières décisions de DjoFin P0",
        "| Date de décision | Action | Date d'exécution | Prix d'exécution |",
        "|---|---|---|---:|",
    ]
    for t in strategy["trades"][:15]:
        action = "Achat" if t["action"] == "buy" else "Vente"
        lines.append(f"| {t['signal_date']} | {action} | {t['date']} | {fmt(t['price'])} € |")
    if not strategy["trades"]:
        lines.append("| — | Aucun ordre | — | — |")
    lines += ["", "## Suite", "Évaluer d'autres périodes, les biais, les coûts et la robustesse avant toute conclusion.", ""]
    target = Path(args.sortie)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(lines), encoding="utf-8")
    target.with_suffix(".json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Rapport généré : {target}")


if __name__ == "__main__":
    main()
