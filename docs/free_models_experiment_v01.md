# DjoFin — modèles gratuits, protocole FREE_ONLY

**Budget autorisé : 0 €**. Les candidats sont identifiés, mais aucun modèle n'est téléchargé ni exécuté à ce stade.

## Candidats
- MiniLM multilingue : similarité de textes, détection de doublons sémantiques.
- mDeBERTa multilingue MNLI : classement zero-shot de titres français/anglais.
- FinBERT : tonalité financière, principalement anglophone ; ne prédit pas les cours.

## Étapes
1. Garder les 40 actualités existantes comme jeu de diagnostic **non indépendant** ; ne pas les présenter comme preuve de généralisation.
2. Constituer un jeu indépendant, annoté à l'aveugle, avec exemples français/anglais, inconnus et cas adversariaux.
3. Mesurer d'abord V0.1 et V0.2 : précision, rappel, erreurs par domaine, temps de calcul.
4. Tester MiniLM **uniquement si** un environnement CPU gratuit disponible et ses quotas sont vérifiés ; télécharger des poids uniquement après validation explicite du lieu d'exécution et de ses conditions.
5. Tester mDeBERTa puis FinBERT de la même façon ; un seul modèle à la fois, CPU, limites mémoire/temps.
6. Conserver le modèle uniquement si gain hors échantillon démontré et coût réel nul.

## Limites techniques
- La politique Python `authorize_operation` est un **garde-fou logiciel**, pas une garantie de facturation de fournisseurs externes. Les restrictions de facturation doivent aussi être configurées dans chaque compte.
- Les offres gratuites peuvent changer et des dépassements peuvent entraîner des coûts selon les comptes ; aucune activation de facturation ni de service GPU.
- Aucun ordre réel, aucune API payante, aucune location GPU, aucun téléchargement automatique de poids.
- Pas de modification du collecteur existant ou des workflows planifiés tant que la faisabilité n'est pas démontrée.

## Prochaine validation
Mesurer les ressources disponibles sur le runner gratuit, vérifier licences et limites d'usage, puis préparer le premier benchmark hors échantillon.
