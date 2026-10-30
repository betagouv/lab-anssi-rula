# Tâche : liste noire et masques obligatoires

Statut : refactor de sobriété validé par contrôles ciblés, prêt à mettre à jour la PR

## Objectif

Permettre de définir des termes sensibles qui sont toujours pseudonymisés dans le transcript et le contexte des nouvelles préparations, puis restent obligatoirement masqués pendant la relecture, la confirmation et les modifications ultérieures.

## Périmètre

- Inclus : CRUD partagé de liste noire, snapshot par préparation, détection dans transcript/contexte, masques obligatoires en relecture et contrôles API avant persistance.
- Exclu : métadonnées, masquage rétroactif des préparations existantes, recalcul des brouillons, prompts Albert supplémentaires, déploiement.

## Critères d'acceptation

- [x] La route `#/liste-noire` et l’API permettent de consulter, ajouter, modifier et supprimer des termes; la liste est initialement vide et reprend les règles Unicode, longueur, conflit de révision et origine de la liste blanche.
- [x] Chaque nouvelle préparation capture une seule fois la liste avant sa mise en file. Ce snapshot est persisté avec le transcript; les anciennes lignes valent vide et une modification ultérieure de la liste n’altère aucun objet existant.
- [x] Les termes noirs sont masqués dans toutes leurs occurrences des textes originaux du transcript et du contexte, après le pipeline Albert et la liste blanche. Ils ne sont jamais ajoutés aux prompts, ne masquent pas les identifiants structurels des locuteurs et ne ciblent pas les métadonnées.
- [x] Les masques noirs sont obligatoires dans la relecture : désactivation/clic et états restaurés ne peuvent enlever leur couverture; catégorie et révélation temporaire restent possibles.
- [x] Confirmation et modification valident les textes finaux avec le snapshot persisté côté serveur. Un snapshot ou historique client falsifié, une plage UTF-16 invalide, une couverture manquante ou la réintroduction d’un terme retourne 422 sans mutation partielle.
- [x] Tests ciblés couvrent Unicode, apostrophes, chevauchements, offsets UTF-16, snapshots asynchrones, maintien des termes à travers confirmation/PUT, migration PostgreSQL et états undo/redo.
- [ ] La baseline liste blanche et les parcours liste noire/relecture avec données synthétiques sont vérifiés dans le navigateur à 390×844 et au moins 1280 px. Ces preuves précèdent le refactor de sobriété et n’ont pas été rejouées.
- [ ] `bash scripts/harness.sh complet` passe avant PR. Le harness complet n’a pas été relancé après le refactor de sobriété, conformément à la demande utilisateur de limiter les contrôles longs.

## Plan

1. Ajouter le modèle, dépôt, service, API, migration, capture et persistance du snapshot, plus l’ADR de non-rétroactivité.
2. Soustraire les termes noirs du texte après la fusion des propositions; préserver les libellés structurels et marquer les masques résultants obligatoires.
3. Ajouter les contrôles de relecture backend, les changements du modèle UI et la page CRUD.
4. Ajouter les tests métier, API, concurrence, snapshots, migration et relecture.
5. Valider l’interface actuelle puis le parcours modifié aux deux dimensions, exécuter les contrôles requis et présenter diff/preuves pour revue Sol.

## Validation

- Refactor PR44 : domaine, dépôt mémoire, dépôt PostgreSQL et handlers CRUD communs paramétrés par la couleur; routes et factories d’injection gardées distinctes. Une page Svelte configurée par couleur remplace les deux pages, avec remount keyed au changement de route. La fusion des positions et le calcul des obligations de relecture sont mutualisés; les comportements snapshot et masques obligatoires restent inchangés.
- `ruff check src tests` : réussi après le refactor.
- `ruff format --check` sur les fichiers Python modifiés : réussi après formatage de cinq fichiers.
- `UV_PROJECT_ENVIRONMENT=/tmp/rula-liste-noire-venv uv run --no-sync mypy` : réussi, 67 fichiers source.
- `UV_PROJECT_ENVIRONMENT=/tmp/rula-liste-noire-venv uv run --no-sync pytest -q tests/api/test_listes.py tests/test_liste_blanche.py tests/test_transcripts_pdf_liste_noire.py tests/test_validation_relecture.py tests/api/test_transcripts_pdf.py` : 38 tests réussis, Python 3.13.11.
- `RULA_TEST_DATABASE_URL=postgresql://… UV_PROJECT_ENVIRONMENT=/tmp/rula-liste-noire-venv uv run --no-sync pytest -q tests/test_migrations.py` : 5 tests réussis sur PostgreSQL jetable `pgvector/pgvector:pg17`, port 65432. Le test de séparation confirme le même terme présent dans les deux tables et inchangé lors d’une modification blanche. Conteneur arrêté après contrôle.
- `pnpm exec vitest run src/transcripts/ListeTermes.test.ts` : 2 tests réussis sur une copie de validation ext4 `/tmp/rula-liste-noire-ui-qa` construite depuis HEAD + diff candidat identique. Le lancement direct depuis `/mnt/c` était bloqué plus de deux minutes en attente `p9_client_rpc`; cette tentative a été interrompue. Aucun `svelte-check`, lint, format UI, build ou harness complet relancé à la demande utilisateur de ne pas rejouer les contrôles UI longs.
- `git diff --check` : réussi.
- Baseline navigateur liste blanche : captures à 1280×900 et 390×844; backend indisponible, réponses 500, donc apparence seule et aucun parcours CRUD prétendu.
- Interface liste noire : parcours réel contre FastAPI et PostgreSQL synthétiques. Ajout desktop à 1280×900; création, modification, conflit de révision obsolète (409) et suppression desktop à 1278×888; création/modification/suppression mobile à 390×844. Sur mobile, `scrollWidth=375` pour `innerWidth=390`.
- Relecture réelle desktop 1280×900 et mobile 390×844 depuis un brouillon synthétique préparé par `ServicePreparationTranscript`/`AdaptateurAlbertDeTest` via bootstrap temporaire même origine. Le bouton « Masque obligatoire — liste noire » est désactivé et les deux occurrences restent masquées; catégorie Secret, annuler/rétablir, sauvegarde API 200 et reprise après rechargement vérifiés. La modal de confirmation affiche que le snapshot de termes reste associé à la source.
- Enregistrement de la fixture dans la base jetable vérifié en base : les deux occurrences d’Alice sont pseudonymisées et `termes_imposes=('Alice',)` est persisté. Le parcours navigateur d’import du fichier PDF lui-même n’a pas été vérifié : l’extension Chrome bloque son mécanisme `setFiles` tant que l’accès aux URL `file:` reste désactivé; cette permission n’a pas été élargie. Aucun fichier réel utilisé.
- Captures navigateur observées en direct par CUA; données de fixture synthétiques uniquement.
- `bash scripts/harness.sh audit` : non requis.

## Décisions

- ADR associée : 0005 — snapshot immuable des termes noirs par préparation.
- Base : `3d7c2e965a1ca22212132ada85ccb9567311b473`, branche `feature/liste-noire`.
- Comparaison cumulative à `origin/main` après refactor (détection de renommages Git normale) : production `+806/-341`, tests `+719/-150`, documentation `+84/-0`; total `+1609/-491`. Avant refactor, le diff était `+1823/-54` (production `+1093`, tests `+648`, documentation `+82`). La baisse nette cumulative est de 651 lignes.

## Handoff

- État du code : refactor intégré au candidat PR44; revue Sol acceptée sous réserve des tests Vitest ciblé et PostgreSQL, tous deux réussis.
- Prochaine action : mettre à jour PR44, puis attendre sa CI et sa revue; la fusion reste une décision humaine.
- Risques ou limites : le workflow d’import de fichier n’a pas été exercé dans le navigateur; la préparation synthétique, la relecture, la sauvegarde, la reprise et la confirmation ont été exercées. La liste noire ne remplace pas la relecture humaine ni les autres protections contre la divulgation.

## Revue indépendante

- Revue initiale du code et preuves de PR44 : ACCEPTE; la revue de sobriété a également accepté le code, sous réserve des tests ciblés.
- Critères revérifiés : tests CRUD paramétrés sur les deux couleurs, isolation Postgres des tables, pipeline noir et validation relecture; Vitest ciblé et cinq tests PostgreSQL réussis.
- Limite : la baseline et le parcours navigateur ainsi que le harness complet n’ont pas été rejoués sur la révision refactorisée, selon la demande utilisateur.
- Verdict : ACCEPTE pour mise à jour de PR44 après tests ciblés; contrôles UI complets/harness non rejoués.
