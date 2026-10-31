"""Frais d'exécution fictifs, calculés avant chaque ordre."""
from dataclasses import dataclass
import math

@dataclass(frozen=True)
class Tarification:
    fixe: float = 0.
    pourcentage: float = .001
    minimum: float = 0.

    def __post_init__(self):
        if any(not math.isfinite(x) or x < 0 for x in (
                self.fixe, self.pourcentage, self.minimum)):
            raise ValueError("Frais invalides")
        if self.pourcentage >= 1:
            raise ValueError("Commission proportionnelle excessive")

def frais_ordre(brut: float, tarif: Tarification) -> float:
    if brut <= 0:
        return 0.
    return max(tarif.minimum, tarif.fixe + brut * tarif.pourcentage)

def montant_achat(budget: float, tarif: Tarification) -> float:
    """Montant brut maximal dont le coût, frais inclus, reste dans le budget."""
    if budget <= tarif.minimum or budget <= tarif.fixe:
        return 0.
    return max(0., min(budget - tarif.minimum,
                       (budget - tarif.fixe) / (1 + tarif.pourcentage)))
