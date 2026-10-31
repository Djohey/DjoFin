# DjoFin — Audit contradictoire préalable (Claude)

Statut : **AUDIT_REQUIS — AUCUN REPLAY IA AUTORISÉ**

## Périmètre à auditer
- tests/fixtures/covid_2020_01_15_asof_v1.json
- tests/fixtures/covid_2020_01_15_market_v1.json
- tests/fixtures/covid_equity_vaccine_study_plan_v1.json
- tests/fixtures/covid_vaccine_event_candidates_v1.json
- tests/fixtures/historical_incidents_v1.json (contrôles techniques secondaires)

## Instructions à l'auditeur indépendant
Tu es un auditeur scientifique, financier et historique **contradictoire**. Ne valide aucune assertion sans preuve primaire datée. Vérifie séparément :
1. L'existence, le contenu, l'URL exacte et la date/heure de publication de chaque source ; signale liens cassés, titres imprécis, révisions rétrospectives et données non accessibles à la date simulée.
2. Les cours de clôture, séries, devises, fuseaux horaires, ajustements dividendes/splits, disponibilité effective après clôture et biais de survivance ; reproduis les calculs et propose des références primaires ou séries fiables.
3. Les annonces des laboratoires (essais, efficacité, échecs, autorisations par juridiction, lancement, pharmacovigilance), partenariats et dates exactes ; distingue signal de sécurité, causalité établie et restriction réglementaire.
4. La **complétude** : acteurs oubliés, annonces concurrentes, indices de référence, secteurs gagnants/perdants, événements de marché simultanés et cas négatifs.
5. Les fuites temporelles : séparer preuves disponibles AVANT chaque cutoff et dénouements révélés APRÈS ; signaler connaissance pré-entraînée impossible à effacer.
6. La validité statistique : fenêtres J+1/J+5/J+20, rendements anormaux, facteurs confondants, taille d'échantillon, multiples tests, surapprentissage et séparation entraînement/test.
7. Les données sensibles : aucune clé API, aucun ordre, aucun secret, aucun appel payant.

## Format obligatoire du rapport
Pour chaque anomalie : identifiant, fichier/champ, constat précis, gravité (bloquant/majeur/mineur), source indépendante avec date, correction recommandée, statut (vérifié/non vérifiable).
Puis fournir : inventaire des sources contrôlées, liste des lacunes, points de désaccord, protocole de reproduction et verdict global **ACCEPTER / CORRIGER / REJETER**.

**Interdiction de conclure ACCEPTER si un événement, une valeur financière ou une date de cutoff majeure n'est pas vérifié.**
Une URL candidate n'est pas une preuve de vérification. Un test logiciel réussi ne valide pas la véracité des données.

## Règle de passage
L'audit doit être effectué indépendamment et son rapport archivé, puis les corrections revérifiées avant gel du jeu de données. L'analyste historique n'a jamais accès au rapport, aux résultats futurs ou aux retours des essais antérieurs. Aucun test Gemini avant validation explicite.
