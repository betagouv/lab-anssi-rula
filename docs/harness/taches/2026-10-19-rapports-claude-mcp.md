# Tâche : consulter et enregistrer les analyses Claude des transcripts confirmés

Statut : PR1 et PR2 livrés en drafts; PR3 en validation; PR4 reste à intégrer.

## Objectif

Permettre à Claude Desktop de lire les transcripts produit et BizDev confirmés, puis d’enregistrer dans RULA des analyses Markdown révisables depuis l’interface, sans remplacer ni appeler Albert.

## Périmètre

- Inclus : historique immuable et idempotent des analyses Claude; catalogue, lecture paginée et consultation REST; trois outils MCP `lister_transcripts`, `lire_transcript` et `enregistrer_analyse`; transport stdio local et transport HTTP authentifié; consultation minimale dans l’écran d’import des transcripts; recette avec données synthétiques; documentation et workflow manuel Clever Cloud.
- Exclu : déploiement ou provisionnement cloud, nouvel addon PostgreSQL, appels à un modèle externe, modification des analyses Albert, lecture des sources non confirmées, migration destructive ou changement de l’anonymisation existante.

## Contrat de données et API

- Une source est éligible si `confirme = TRUE` et `type_source IN ('produit', 'bizdev')`.
- L’empreinte SHA-256 est calculée côté serveur sur une représentation canonique de `type_source`, `contenu`, `contexte` et `locuteurs`.
- `rapports_claude` conserve `id`, `transcript_id` avec cascade à la suppression, révision, empreinte, clé UUID globalement unique, Markdown et date serveur. Les rapports sont immuables; une modification de source les rend obsolètes sans les modifier. Le statut courant du catalogue est dérivé de la révision, que le dépôt PDF incrémente lors de toute modification applicative; l’empreinte protège les lectures par blocs et les écritures. Les analyses Albert ne participent pas à ce statut.
- L’écriture exige une clé UUID, la révision et l’empreinte observées. Une clé réutilisée pour la même requête retourne le même rapport, même après modification de source; la même clé pour une requête différente produit un conflit. Une nouvelle clé vérifie sous verrou l’éligibilité, la révision et l’empreinte avant insertion. Le Markdown doit être non blanc et contenir au plus 200 000 caractères.
- Le catalogue ordonne les IDs de transcript par ordre croissant, pages de 20 par défaut et 100 au maximum, avec filtres produit, projet, type et statut `tous|analyses|non_analyses`. Il ne retourne ni titre, ni nom de fichier, ni nom de produit, ni contenu.
- La lecture source assemble contexte et transcript avec des séparateurs explicites, renvoie la longueur totale et des blocs d’au plus 30 000 caractères Unicode. Après le premier bloc, chaque lecture exige révision et empreinte; toute modification rend la lecture conflictuelle. L’historique est paginé en métadonnées; un rapport est lu par blocs avec état courant ou obsolète.
- Les lectures REST restent dans le périmètre de l’API RULA : `GET /api/rapports-claude/transcripts`, `GET /api/rapports-claude/transcripts/{id}`, `GET /api/rapports-claude/transcripts/{id}/rapports` et `GET /api/rapports-claude/{rapport_id}`. Le POC local n’a pas d’authentification applicative; l’accès public n’est autorisé que derrière la protection HTTP Basic Clever existante. L’écriture reste réservée à MCP.
- Le serveur MCP expose exactement ces trois outils. `lire_transcript` prend le mode explicite `source|historique|rapport`. Le transport stdio local utilise la configuration PostgreSQL RULA; le transport HTTP stateless `/mcp` exige un bearer secret comparé en temps constant sur toute route hors santé minimale, échoue au démarrage si le secret manque et ne journalise jamais ce secret.

## Critères d’acceptation

- [ ] La migration additive n’efface aucune donnée, conserve l’historique et cascade uniquement à la suppression du transcript.
- [ ] Le domaine distingue source absente, source non éligible, source modifiée et conflit d’idempotence; les tests métier couvrent replay, conflit de clé, obsolescence et limites Markdown.
- [ ] Une modification du transcript via le parcours PDF augmente sa révision, rend l’ancien rapport obsolète et réintègre la source au filtre « non analysées ».
- [ ] Les dépôts PostgreSQL ouvrent une connexion par opération et ne partagent pas de connexion mutable.
- [ ] Les routes REST exposent seulement les métadonnées nécessaires et des lectures paginées/bloc par bloc.
- [ ] Le serveur MCP implémente les trois outils en stdio et HTTP; les tests de protocole vérifient authentification absente/incorrecte/correcte, blocs, écriture et persistance après redémarrage.
- [x] L’interface permet de retrouver un rapport, son statut courant/obsolète et sa date; le Markdown est affiché comme texte échappé.
- [x] La recette de bout en bout synthétique couvre anonymisation test, confirmation API, catalogue MCP, écriture et relecture du rapport dans RULA sans appel réseau Albert.
- [ ] Le workflow manuel et le runbook isolent les identifiants de l’application MCP des secrets DEMO et n’effectuent aucun déploiement dans cette tâche.
- [ ] Les branches stacked déclenchent la CI PR. Les contrôles backend et frontend requis passent avant chaque PR.

## Plan

1. Ajouter le domaine, le dépôt de test, l’adaptateur PostgreSQL, la migration additive et les lectures REST.
2. Ajouter les transports MCP stdio et HTTP autour d’une factory d’outils partagée et valider le protocole.
3. Rendre les rapports retrouvables dans l’écran de transcript et exécuter la recette synthétique intégrée.
4. Documenter la configuration d’exploitation et ajouter un workflow manuel séparé, sans provisionner ni déployer.

## Validation

- `bash scripts/harness.sh complet --cible backend` : Ruff et mypy réussis; 341 tests passés, 4 intégrations ignorées.
- `NODE_OPTIONS=--experimental-global-webcrypto bash scripts/harness.sh complet --cible frontend` : sous WSL Node 24.13.0, 18 suites/101 tests passés, svelte-check sans erreur ni avertissement, `pnpm check`, ESLint, Prettier et build Vite réussis. L’option compense le global WebCrypto manquant dans l’isolate Vitest de ce runtime local.
- `RULA_TEST_POSTGRES=1 uv run pytest tests/integration/test_rapports_claude_postgres.py -q` sur la base dédiée `rula_mcp_test` (`127.0.0.1:55432`) : 3 tests passés, dont client MCP stdio réel avec écriture PostgreSQL puis relecture depuis un second processus; cette base contient uniquement les données synthétiques du test.
- Le scénario intégré PR3 exécute l’upload PDF avec `AdaptateurAlbertDeTest`, vérifie que la source pseudonymisée n’apparaît au catalogue qu’après confirmation API, puis la lit et écrit un rapport via le client MCP avant relecture REST. `PYTHONPATH=.:src RULA_TEST_POSTGRES=1 uv run pytest tests/integration/test_rapports_claude_postgres.py -q` : 4 tests passés en 24,18 s sur la base dédiée; aucune requête Albert externe.
- PR3 corrige également les pages complètes du catalogue et de l’historique, ajoute l’actualisation manuelle et distingue une erreur de chargement de l’état « à analyser ». Une actualisation recharge aussi le rapport ouvert pour éviter un statut courant périmé. La confirmation de recette utilise une date synthétique explicite.
- Le harness backend PR3 est passé : `ruff check src/ tests/`, mypy sur 146 modules, puis `pytest -q` avec 345 tests passés et 6 ignorés; les 4 intégrations PostgreSQL dédiées passent séparément. `tests/test_serveur_mcp.py` vérifie le client SDK officiel v2, les trois outils, l’idempotence et les réponses HTTP sans bearer, avec bearer faux et valide.
- Frontend inchangé revalidé sous WSL Node 24.13.0 et ses dépendances Linux existantes : 18 suites / 101 tests, Svelte-check (0 erreur, 0 avertissement), `pnpm check`, lint, format et build Vite réussis. `NODE_OPTIONS=--experimental-global-webcrypto` est requis par l’isolate Vitest local.
- Harness frontend PR3 sous WSL Node 24.13.0 : `NODE_OPTIONS=--experimental-global-webcrypto pnpm check` (Svelte-check 0 erreur/avertissement et TypeScript), `pnpm lint:check`, `pnpm format:check`, `pnpm test` (19 suites, 102 tests) et `pnpm build` réussis. Les dépendances Linux isolées du worktree ont été réutilisées.
- La CI utilise le service éphémère `pgvector/pgvector:pg17`, applique les migrations puis exécute ces intégrations dans une étape isolée. La CI distante n’a pas encore été exécutée.
- `bash scripts/harness.sh audit` : non requis.
- Tests d’intégration PostgreSQL exécutés uniquement sur la base dédiée du worktree; identité `rula_mcp_test|rula_test|5432`, tables initialement vides, extension `vector` disponible.

## Décisions

- ADR associée : [0004 — Rapports Claude et accès MCP](../../adr/0004-rapports-claude-mcp.md).
- Ordre des PR : `feature/rapports-claude` → `feature/mcp-transcripts` → `feature/parcours-rapports-claude` → `ops/deploiement-mcp-clever`. Aucune fusion ni exécution de déploiement n’est incluse.

## Handoff

- État du code : PR1 domaine/API et PR2 transports MCP relus par Sol; PR3 consultation et recette validées par Sol, contrôles complets réussis avant draft. Worktree `D:\RULA-mcp-integration-20261019`, branche PR3 `feature/parcours-rapports-claude` empilée sur PR2 `feature/mcp-transcripts` et PR1 `feature/rapports-claude`.
- PR2 expose `python -m serveur_mcp` en stdio et `serveur_mcp:app` en HTTP `/mcp`; `/healthz` est public, les autres chemins exigent un bearer constant-time, et chaque transport vérifie en lecture seule les colonnes nécessaires avant de servir. Aucun transport ne lance de migration.
- Prochaine action : terminer les contrôles frontend complets, puis ouvrir le draft PR3; intégrer ensuite les trois fichiers préparés pour PR4 après leurs corrections de revue.
- Risques ou limites : CI distante non exécutée; `pgdata/` est la base jetable locale du conteneur, reste hors staging. Le POC local n’ajoute pas d’authentification applicative à RULA.

## Revue indépendante

- Diff examiné :
- Critères vérifiés :
- Remarques :
- Verdict :
