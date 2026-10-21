# Tâche : recentrer RULA sur la pseudonymisation de PDF

Statut : PR #41 ouverte; écran de relecture validé en local

## Objectif

Livrer une application accessible et réactive dédiée à l’import, la relecture humaine, la confirmation, la consultation, le téléchargement et la suppression de transcripts PDF pseudonymisés pour MSS et MSC.

## Périmètre

- Inclus : choix MSS/MSC; progression et reprise de préparation; édition des six catégories et des locuteurs; confirmation définitive; historique; consultation, téléchargement et suppression; interface DSFR avec thème sombre; migration des données applicatives.
- Exclu : parcours d’analyse, projets, FeatureBase, collecte distincte de retours BizDev, données hors MSS/MSC et sauvegardes Clever Cloud.

## Critères d'acceptation

- [ ] L’import et la préparation du PDF exposent une progression récupérable et la source originale reste temporaire.
- [ ] La relecture permet de corriger les six catégories et les locuteurs avant confirmation.
- [x] Après une préparation terminée, l’étape 2 affiche le transcript et le panneau de relecture, même si le serveur ne fournit pas encore d’état de relecture.
- [ ] La confirmation persiste le contenu pseudonymisé; liste, consultation, PDF téléchargé et suppression opèrent sur la source confirmée.
- [ ] Liste et fichier exporté portent un nom commençant par `pseudonymiser_` sans duplication.
- [ ] L’interface respecte le prototype de référence, DSFR, le clavier, le thème sombre et les viewports 390×844 et ≥1280 px.
- [ ] L’interface et l’API ne proposent plus les analyses, projets, FeatureBase, ni les parcours correspondants.
- [ ] La migration conserve les produits MSS/MSC et seulement les lignes PDF confirmées `type_source IN ('produit','bizdev')` rattachées à ces produits, avec les identifiants et données métier nécessaires.
- [x] La migration fonctionne sur base existante et vide, est idempotente via le runner, et sa transaction peut être annulée sans laisser un schéma partiel.
- [ ] Les étapes de maintenance, d’exécution et de restauration sont documentées; déploiement après checks verts et revue Sol.

## Plan

1. Réduire les services et routes au parcours de pseudonymisation PDF.
2. Recentrer l’interface sur MSS/MSC et supprimer les parcours hors périmètre.
3. Ajouter la migration transactionnelle et documenter la maintenance et le rollback par restauration.
4. Exécuter les contrôles requis et vérifier les parcours desktop/mobile ainsi que le PDF réel.
5. PR #41 ouverte après validation locale de l’écran de relecture. L’utilisateur autorise le déploiement après checks verts; demander la revue Sol avant fusion.

## Validation

- Commandes ciblées pendant l’itération : à consigner.
- `bash scripts/harness.sh complet` : le lancement initial a été bloqué par le lien `.venv/lib64` en accès refusé. Avec `UV_PROJECT_ENVIRONMENT` isolé dans `%LOCALAPPDATA%\Temp`, Ruff et mypy passent et pytest donne 99 réussis, 3 ignorés. Le harness s’arrête ensuite car `svelte-check` manque dans le worktree Linux.
- Frontend Windows : `pnpm install --frozen-lockfile`, `pnpm test` (9 fichiers, 37 tests), `pnpm check` (0 erreur/avertissement), `pnpm lint:check`, `pnpm format:check` et `pnpm build` passent.
- Migration sur PostgreSQL isolé : `RULA_TEST_DATABASE_URL=… uv run pytest tests/test_migrations.py -q` passe (3 tests : base vide/idempotence, conservation des lignes qualifiées, rollback transactionnel).
- Parcours navigateur : l’utilisateur a confirmé que l’écran de relecture s’affiche après import. Les autres parcours et les viewports 390×844 et ≥1280 px restent à vérifier.
- Téléchargement et rendu du PDF : non vérifié dans ce handoff.

## Décisions

- ADR associée : [0004 — Réduire RULA à la pseudonymisation de PDF](../../adr/0004-pseudonymisation-seule.md).
- La migration ne préserve que des lignes confirmées Produit/BizDev rattachées à MSS ou MSC; `confirme=TRUE` seul ne qualifie pas une ligne.
- Le hook post-build Clever Cloud migre avant de lancer le nouveau runtime; la bascule exige l’arrêt des instances précédentes et une fenêtre de maintenance coordonnée.

## Handoff

- État du code : implémentation dans le worktree isolé `feature/pseudonymisation-seule`, poussée dans la PR #41 (https://github.com/betagouv/lab-anssi-rula/pull/41); l’utilisateur a confirmé que l’écran de relecture apparaît dans le preview local sur le port 5173. Aucun déploiement n’a été effectué.
- Prochaine action : attendre les checks GitHub, compléter les vérifications navigateur restantes et demander la revue Sol avant fusion et déploiement. La correction initialise l’état depuis les occurrences quand le serveur n’a pas encore d’état de relecture, et conserve les choix déjà sauvegardés.
- Risques ou limites : migration destructive sur la base active; déploiement après checks verts et revue Sol. Les sauvegardes ne sont pas modifiées. Aucun PDF d’exemple n’a été trouvé; aucun fichier n’a été envoyé à Albert par ce handoff.

## Revue indépendante

- Diff examiné : l’affichage du composant de relecture ne dépend plus de `etatRelecture`; le modèle reconstruit les masques depuis les occurrences au montage.
- Critères vérifiés : en attente.
- Remarques : en attente.
- Verdict : en attente.
