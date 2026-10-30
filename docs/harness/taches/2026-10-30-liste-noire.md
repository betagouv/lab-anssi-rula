# Tâche : liste noire et masques obligatoires

Statut : prête pour PR

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
- [x] La baseline liste blanche et les parcours liste noire/relecture avec données synthétiques sont vérifiés dans le navigateur à 390×844 et au moins 1280 px.
- [x] `bash scripts/harness.sh complet` et l’intégration PostgreSQL sur base dédiée passent avant PR.

## Plan

1. Ajouter le modèle, dépôt, service, API, migration, capture et persistance du snapshot, plus l’ADR de non-rétroactivité.
2. Soustraire les termes noirs du texte après la fusion des propositions; préserver les libellés structurels et marquer les masques résultants obligatoires.
3. Ajouter les contrôles de relecture backend, les changements du modèle UI et la page CRUD.
4. Ajouter les tests métier, API, concurrence, snapshots, migration et relecture.
5. Valider l’interface actuelle puis le parcours modifié aux deux dimensions, exécuter les contrôles requis et présenter diff/preuves pour revue Sol.

## Validation

- `uv run ruff check src tests` : réussi.
- `uv run mypy` : réussi sur 73 fichiers source.
- `uv run pytest -q tests/test_transcripts_pdf_liste_noire.py tests/test_validation_relecture.py` : 9 tests réussis après ajout du cas de terme chevauchant le préfixe locuteur.
- `RULA_TEST_DATABASE_URL=postgresql://… uv run pytest -q tests/test_migrations.py::test_migration_liste_noire_conserve_les_snapshots_et_est_idempotente` : réussi sur PostgreSQL jetable, ajout réel du snapshot `('Alice',)`, lecture JSONB en tuple, listing et conservation après `modifier`.
- Premier `bash scripts/harness.sh complet` : backend réussi (144 tests), tests/check/lint UI réussis; `format:check` a demandé le formatage Prettier de 5 fichiers UI. Aucun problème logique.
- Dernier `NODE_OPTIONS=--experimental-global-webcrypto RULA_TEST_DATABASE_URL=postgresql://… bash scripts/harness.sh complet` : réussi, code 0. `ruff check .`, mypy, 144 tests backend (5 tests de migrations), 42 tests frontend, `pnpm check`, `pnpm lint:check`, `pnpm format:check` et `pnpm build` réussis. `svelte-check` : 0 erreur/avertissement. Un avertissement préexistant de dépréciation Starlette/httpx apparaît pendant pytest.
- Intégration PostgreSQL : base dédiée `rula-liste-noire-pgtest`, image `pgvector/pgvector:pg17`, port local `65432`; migrations et tests lancés par le harness.
- Baseline navigateur liste blanche : captures à 1280×900 et 390×844; backend indisponible, réponses 500, donc apparence seule et aucun parcours CRUD prétendu.
- Interface liste noire : parcours réel contre FastAPI et PostgreSQL synthétiques. Ajout desktop à 1280×900; création, modification, conflit de révision obsolète (409) et suppression desktop à 1278×888; création/modification/suppression mobile à 390×844. Sur mobile, `scrollWidth=375` pour `innerWidth=390`.
- Relecture réelle desktop 1280×900 et mobile 390×844 depuis un brouillon synthétique préparé par `ServicePreparationTranscript`/`AdaptateurAlbertDeTest` via bootstrap temporaire même origine. Le bouton « Masque obligatoire — liste noire » est désactivé et les deux occurrences restent masquées; catégorie Secret, annuler/rétablir, sauvegarde API 200 et reprise après rechargement vérifiés. La modal de confirmation affiche que le snapshot de termes reste associé à la source.
- Enregistrement de la fixture dans la base jetable vérifié en base : les deux occurrences d’Alice sont pseudonymisées et `termes_imposes=('Alice',)` est persisté. Le parcours navigateur d’import du fichier PDF lui-même n’a pas été vérifié : l’extension Chrome bloque son mécanisme `setFiles` tant que l’accès aux URL `file:` reste désactivé; cette permission n’a pas été élargie. Aucun fichier réel utilisé.
- Captures navigateur observées en direct par CUA; données de fixture synthétiques uniquement.
- `bash scripts/harness.sh audit` : non requis.

## Décisions

- ADR associée : 0005 — snapshot immuable des termes noirs par préparation.
- Base : `3d7c2e965a1ca22212132ada85ccb9567311b473`, branche `feature/liste-noire`.

## Handoff

- État du code : implémentation, contrôles et revue Sol terminés; prêt pour commit/PR.
- Prochaine action : ouvrir la PR vers `main`, attendre sa revue et sa CI, puis laisser la décision de fusion à l’utilisateur.
- Risques ou limites : le workflow d’import de fichier n’a pas été exercé dans le navigateur; la préparation synthétique, la relecture, la sauvegarde, la reprise et la confirmation ont été exercées. La liste noire ne remplace pas la relecture humaine ni les autres protections contre la divulgation.

## Revue indépendante

- Diff examiné par Sol; les constats ont été corrigés : le préfixe structurel `SPEAKER_XX:` reste intact tandis que le texte noir qui le suit est masqué; la confirmation précise que le snapshot reste associé à la source; le pragma de couverture ajouté a été retiré.
- Critères vérifiés : tests pipeline et garde finale pour le chevauchement préfixe/terme, roundtrip PG non vide, état de relecture obligatoire en direct et API.
- Remarques : le formatage Prettier a été appliqué aux cinq fichiers UI demandés par `format:check`.
- Verdict : ACCEPTE — code et preuves; harness complet final réussi, code 0.
