# DjoFin — Veille V0 : collecte sans décision

Statut : SPECIFICATION — aucune exécution planifiée ou appel API déployé.

## Mission
Collecter et classer des faits contemporains sans investissement ni prédiction automatique. Priorités : 1 finance, 2 géopolitique, 3 technologie/innovation ; santé/pharma en transversal.

## Répertoire initial des sources
- Marchés et dépôts : SEC EDGAR (sec.gov/edgar), AMF (amf-france.org), Euronext (euronext.com), Nasdaq (nasdaq.com).
- Macro : BCE (ecb.europa.eu), Fed (federalreserve.gov), Eurostat (ec.europa.eu/eurostat), INSEE (insee.fr), BLS (bls.gov).
- Santé : ClinicalTrials.gov, EMA (ema.europa.eu), FDA (fda.gov), OMS (who.int), ANSM (ansm.sante.fr).
- Géopolitique : Conseil UE (consilium.europa.eu), Commission européenne (commission.europa.eu), ONU (un.org), OFAC (ofac.treasury.gov).
- Tech : arXiv (arxiv.org), USPTO (uspto.gov), EPO (epo.org), communiqués investisseurs officiels.
Ces domaines sont des pistes à contrôler (RSS, API, licence, fréquence, coût), non des connecteurs déjà activés.

## Collecte
1. Détecter via flux officiels RSS/API publics, si autorisés et gratuits ; respecter conditions d'usage et quotas.
2. Enregistrer identifiant stable, URL, organisme, titre original, date publication et récupération UTC, langue, version/empreinte, périmètre géographique.
3. Conserver le brut et les versions successives ; ne jamais remplacer silencieusement une publication modifiée.
4. Dédupliquer par URL canonique et empreinte ; relier les reprises au communiqué initial.
5. Classer le thème, l'entreprise, le ticker avec marché et degré de certitude ; ne pas inventer de correspondances.
6. Évaluer fiabilité, nouveauté, matérialité, urgence et coût ; classer en à approfondir / veille / bruit.
7. Croiser au moins une autre source indépendante pour les faits à fort impact, distinguer confirmation et simple reprise.
8. Archiver hypothèses, inconnues, contradictions et recherches abandonnées.
9. Créer une alerte explicable avec source, date, incertitude et raison ; aucune recommandation d'ordre.
10. Produire un journal d'exécution (erreurs, couverture, latence, coûts, articles ignorés).

## Contraintes de démarrage
- FREE_ONLY, pas de services payants, pas de clés dans le dépôt.
- Pas de courtier, pas de transaction, pas de décision d'achat automatique.
- Les cours gratuits peuvent être différés : afficher la latence et la provenance.
- Séparer strictement la veille courante des dossiers historiques point-in-time.
- Démarrer par quelques flux officiels et mesurer le rapport signal/bruit avant élargissement.
- Exécution périodique GitHub Actions envisagée mais NON configurée ici : fréquence et quotas à valider.

## Critères d'acceptation du premier collecteur
- Zéro fuite de secrets ; zéro coût non approuvé.
- Chaque entrée possède URL, source, publication UTC (ou précision indiquée), récupération UTC, empreinte et statut de vérification.
- Reprises identifiées, erreurs journalisées, sources indisponibles signalées.
- Une alerte ne peut pas être qualifiée de vérifiée si sa source primaire n'a pas été contrôlée.
