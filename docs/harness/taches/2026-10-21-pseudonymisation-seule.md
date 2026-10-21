# Tâche : recentrer RULA sur la pseudonymisation de PDF

Statut : PR #41 ouverte; écran de relecture validé en local

## Objectif

Livrer une application accessible et réactive dédiée à l’import, la relecture humaine, la confirmation, la consultation, le téléchargement et la suppression de transcripts PDF pseudonymisés pour MSS et MSC.

## Périmètre

- Inclus : choix MSS/MSC; progression et reprise de préparation; édition des six catégories et des locuteurs; confirmation définitive; historique; consultation, téléchargement et suppression; interface DSFR avec thème sombre; migration des données applicatives.
- Exclu : parcours d’analyse, projets, FeatureBase, collecte distincte de retours BizDev, données hors MSS/MSC et sauvegardes Clever Cloud.

## Critères d'acceptation

- [x] L’import et la préparation du PDF exposent une progression récupérable et la source originale reste temporaire.
- [ ] La relecture permet de corriger les six catégories et les locuteurs avant confirmation.
- [x] Après une préparation terminée, l’étape 2 affiche le transcript et le panneau de relecture, même si le serveur ne fournit pas encore d’état de relecture.
- [x] La confirmation persiste le contenu pseudonymisé; liste, consultation, PDF téléchargé et suppression opèrent sur la source confirmée.
- [x] Liste et fichier exporté portent un nom commençant par `pseudonymiser_` sans duplication.
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
- CI GitHub pour `7a2df89d707cfa21ee46030a339bdad4294e205c` : `Backend Python` passe (`uv sync --locked`, `uv run ruff check .`, `uv run mypy`, `uv run pytest`); `Frontend Svelte` passe (`corepack enable && pnpm install --frozen-lockfile`, `pnpm test`, `pnpm check`, `pnpm lint:check`, `pnpm format:check`, `pnpm build`). Les contrôles CodeQL `Analyze (actions)`, `Analyze (javascript-typescript)`, `Analyze (python)` et `CodeQL` passent. Au relevé du 21 octobre 2026, `GitGuardian Security Checks` est encore en cours. Aucun nouveau test local n’a été exécuté pour cette mise à jour documentaire.
- Frontend Windows : `pnpm install --frozen-lockfile`, `pnpm test` (9 fichiers, 37 tests), `pnpm check` (0 erreur/avertissement), `pnpm lint:check`, `pnpm format:check` et `pnpm build` passent.
- Migration sur PostgreSQL isolé : `RULA_TEST_DATABASE_URL=… uv run pytest tests/test_migrations.py -q` passe (3 tests : base vide/idempotence, conservation des lignes qualifiées, rollback transactionnel).
- Couverture ciblée renforcée : `RULA_TEST_DATABASE_URL=… uv run pytest tests/api/test_transcripts_pdf.py tests/test_migrations.py -q` passe (6 tests). La migration conserve quatre lignes PDF confirmées admissibles (Produit et BizDev pour MSS et MSC), leurs identifiants et données métier, et exclut lignes non confirmées, type UX, produit MQC et produit nul. Le même lot vérifie l’import, l’état terminé/reprise, l’enregistrement et la restitution de la relecture, la confirmation du contenu final soumis, les erreurs d’import, l’expiration, les listes isolées par MSS/MSC, le détail, la modification, la suppression et le téléchargement PDF avec préfixe sans doublon. PostgreSQL de test jetable sur le port 55432; la stack de preview n’a pas été touchée.
- Contrôles backend ciblés après ajout : `uv run ruff check tests/api/test_transcripts_pdf.py tests/test_migrations.py` passe; `uv run ruff format --check tests/api/test_transcripts_pdf.py tests/test_migrations.py` passe; `uv run mypy` passe (53 fichiers).
- Limite de confirmation : l’API valide le statut/préparation, le produit, le type et la structure, puis persiste le contenu final explicitement soumis par le client. Le client peut désactiver des masques; le serveur ne garantit donc pas l’absence de données personnelles dans le contenu confirmé.
- Preuve navigateur sur le preview local : aux viewports 390×844 et 1280×900, l’historique ne déborde pas horizontalement. Le choix MSS est accessible au clavier. Un PDF synthétique sans donnée utilisateur suit l’import et la progression jusqu’à la relecture; l’écran présente trois masques, puis le bouton de confirmation ouvre son dialogue. Après confirmation, l’historique MSS contient l’enregistrement, sa consultation fonctionne et le PDF a été téléchargé réellement. Ces contrôles ne constituent pas un audit complet du clavier ni une preuve de correction manuelle des six catégories.
- Inspection du PDF téléchargé avec `pypdf` : le contenu textuel extrait conserve les trois masques, ne contient pas les valeurs source ni de rubrique d’analyse, et le nom `pseudonymiser_…pdf` ne duplique pas le préfixe. La mise en page visuelle du PDF n’a pas été inspectée. Le PDF utilisé était synthétique et n’a pas été envoyé à Albert.
- La base du preview contenait déjà trois enregistrements MSC; ils ont été laissés intacts. Un enregistrement MSS synthétique est conservé dans le preview pour inspection par l’utilisateur.

## Décisions

- ADR associée : [0004 — Réduire RULA à la pseudonymisation de PDF](../../adr/0004-pseudonymisation-seule.md).
- La migration ne préserve que des lignes confirmées Produit/BizDev rattachées à MSS ou MSC; `confirme=TRUE` seul ne qualifie pas une ligne.
- Le hook post-build Clever Cloud migre avant de lancer le nouveau runtime; la bascule exige l’arrêt des instances précédentes et une fenêtre de maintenance coordonnée.

## Handoff

- État du code : implémentation dans le worktree isolé `feature/pseudonymisation-seule`, poussée dans la PR #41 (https://github.com/betagouv/lab-anssi-rula/pull/41). Le preview local sur le port 5173 conserve trois entrées MSC préexistantes et une entrée MSS synthétique pour inspection. Aucun déploiement n’a été effectué.
- Prochaine action : attendre les checks GitHub de la révision finale, puis satisfaire les prérequis opérationnels avant tout déploiement : sauvegarde de la base, arrêt des anciennes instances et exécution dans une fenêtre de maintenance coordonnée. Les validations navigateur demandées sont terminées. La correction initialise l’état depuis les occurrences quand le serveur n’a pas encore d’état de relecture, et conserve les choix déjà sauvegardés.
- Risques ou limites : migration destructive sur la base active; aucune migration de production ni aucun déploiement n’a été exécuté. Les sauvegardes Clever Cloud ne sont pas dans le périmètre de modification. Aucun PDF d’exemple n’a été trouvé; aucun fichier n’a été envoyé à Albert par ce handoff.

## Revue indépendante

- Diff examiné : SHA `bb194155d059c6a2c12619510f65b7d967fbd784`.
- Critères vérifiés : parcours de pseudonymisation PDF et couverture associée; les checks CI de cette révision finale restent attendus.
- Remarques : P2 — la preuve de débordement porte sur la vue historique, et la navigation clavier vérifie le choix MSS uniquement. Aucun audit clavier complet, aucune correction manuelle vérifiée des six catégories et aucune inspection visuelle de la mise en page du PDF. `pypdf` vérifie seulement le texte extrait du fichier téléchargé.
- Verdict : accepté sous réserve de CI verte.
