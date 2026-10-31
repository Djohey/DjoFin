# DjoFin — architecture évolutive contrôlée (V0.1)

**Statut : architecture validée, implémentation progressive.** Ce document n'affirme pas que DjoFin apprend déjà de manière autonome.

## Mission
Transformer les publications publiques en hypothèses vérifiables, puis mesurer leur utilité pour la recherche financière, géopolitique et technologique. Priorités : finance, géopolitique, technologies ; pharmacie comme domaine transversal. Aucune décision d'investissement automatique.

## Boucle d'évolution
1. **Observer** : conserver la publication brute, l'URL, la date de collecte, l'origine et la version du collecteur.
2. **Comprendre / reconnaître l'inconnu** : identifier les domaines, entités, ambiguïtés et lacunes. Les sujets inconnus ne sont pas classés « sans intérêt » par défaut.
3. **Émettre une hypothèse** : proposition réfutable, horizon temporel, mécanisme causal, preuves pour/contre, degré d'incertitude.
4. **Tester** : séparation stricte des informations disponibles à la date de décision et des résultats ultérieurs ; comparaison à une méthode de référence simple.
5. **Critiquer** : mesurer les faux positifs, faux négatifs, événements manqués, délais de détection, coûts et dérives.
6. **Proposer une évolution** : enregistrer les changements de règles et les motifs ; ne pas modifier silencieusement la méthode active.
7. **Promouvoir ou rejeter** : tests indépendants hors échantillon, revue humaine, version publiée, possibilité de revenir en arrière.

## Gouvernance
- Une **version stable** est figée et utilisée comme référence.
- Une **version candidate** peut être testée sur des données historiques ou futures isolées.
- Promotion uniquement après preuve de gain robuste sur des critères préalablement définis.
- Toute modification conserve : auteur/provenance, date, diff, hypothèse, résultats des tests, risques, coût, décision et version antérieure.
- Aucun déploiement automatique de nouveaux prompts, sources, stratégies ou modèles sans contrôles adaptés.
- Aucun ordre réel, appel payant ou usage de secrets sans autorisation explicite.

## Mesures
- **Précision de la sélection** : proportion des alertes pertinentes parmi les alertes émises.
- **Rappel** : proportion des événements importants effectivement repérés, y compris ceux hors sélection.
- **Délai** : temps entre la première publication accessible et la détection.
- **Calibration** : correspondance entre niveau de confiance et fréquence de réussite.
- **Robustesse** : performance sur d'autres périodes, secteurs et sources.
- **Coût** : requêtes, temps machine, stockage et éventuels appels de modèles.
- **Couverture des inconnus** : taux d'exploration et découvertes utiles hors catégories connues.

L'« importance » doit être définie avant les tests, avec plusieurs évaluateurs si possible. Les variations de cours ne suffisent pas à démontrer la causalité ou la pertinence.

## Première implémentation
`djofin/research_priority.py` est un **filtre déterministe exploratoire**, pas un moteur d'intelligence ni une mesure validée de pertinence. Il attribue `review`, `routine` ou `explore` et conserve les sujets inconnus. Pas de score arbitraire sur 100, pas de signal d'achat/vente.

## Travaux restants
- Tester le filtre sur le flux collecté et mesurer le taux de sujets inconnus.
- Constituer des cas de référence annotés **sans regarder les résultats futurs**.
- Échantillonner aléatoirement les éléments « routine » pour rechercher les faux négatifs.
- Journal des hypothèses, versionnement des expérimentations et registre des décisions.
- Replays point-in-time uniquement après authentification des archives antérieures au cutoff.
- Brancher la classification sur la collecte après validation ; aucun agent autonome actif à ce stade.
