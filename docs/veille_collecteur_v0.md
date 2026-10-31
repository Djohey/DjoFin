# Veille DjoFin V0 — mode manuel, gratuit

Deux flux de départ : BCE (communiqués) et SEC (communiqués). Ils sont à vérifier en conditions d'exécution : l'existence de pages RSS officielles ne garantit pas que chaque URL configurée fonctionne sans restrictions.

Exécution depuis la racine du dépôt : `python scripts/collect_public_feeds.py --output data/news/news.jsonl`.

Sortie : fichier JSONL append-only avec URL, titre, horodatage brut du flux, date de collecte UTC, identifiant stable, statut non vérifié. Les erreurs par flux sont affichées et provoquent un code de sortie non nul, même si les autres flux réussissent.

**Pas encore de tâche planifiée, d'alertes push, de base Supabase, de collecte continue, de cours de marché ou de modèle IA.** Les données sont enregistrées uniquement là où le script s'exécute ; une exécution éphémère GitHub Actions sans artefact ou base de données ne conserverait pas durablement l'historique.

Limites : les dates RSS ne sont pas encore normalisées ; le hachage dépend du titre et de la date et une mise à jour peut produire une nouvelle entrée. La qualité des flux, les conditions d'utilisation et les fréquences doivent être testées avant toute automatisation.

Prochaine étape : exécuter le script dans un environnement réseau autorisé, vérifier les erreurs réelles, puis ajouter un stockage persistant et un horaire raisonnable après validation.
