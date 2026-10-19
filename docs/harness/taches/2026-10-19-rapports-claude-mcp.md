# Tâche : consulter et enregistrer les analyses Claude des transcripts confirmés

Statut : PR #36–#39 sont des drafts empilés; leurs contrôles CI sont tous verts et Sol a accepté les quatre lots. Aucun PR n’est fusionné et aucun déploiement ni provisionnement cloud n’a été effectué.

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

- [x] La migration additive n’efface aucune donnée, conserve l’historique et cascade uniquement à la suppression du transcript.
- [x] Le domaine distingue source absente, source non éligible, source modifiée et conflit d’idempotence; les tests métier couvrent replay, conflit de clé, obsolescence et limites Markdown.
- [x] Une modification du transcript via le parcours PDF augmente sa révision, rend l’ancien rapport obsolète et réintègre la source au filtre « non analysées ».
- [x] Les dépôts PostgreSQL ouvrent une connexion par opération et ne partagent pas de connexion mutable.
- [x] Les routes REST exposent seulement les métadonnées nécessaires et des lectures paginées/bloc par bloc.
- [x] Le serveur MCP implémente les trois outils en stdio et HTTP; les tests de protocole vérifient authentification absente/incorrecte/correcte, blocs, écriture et persistance après redémarrage.
- [x] L’interface permet de retrouver un rapport, son statut courant/obsolète et sa date; le Markdown est affiché comme texte échappé.
- [x] La recette de bout en bout synthétique couvre anonymisation test, confirmation API, catalogue MCP, écriture et relecture du rapport dans RULA sans appel réseau Albert.
- [x] Le workflow manuel et le runbook isolent les identifiants de l’application MCP des secrets DEMO et n’effectuent aucun déploiement dans cette tâche.
- [x] Les branches stacked déclenchent la CI PR. Les contrôles backend et frontend requis passent avant chaque PR.

- [x] La recette réelle Claude Desktop en stdio lit une source BizDev pseudonymisée, écrit un rapport et le relit; PostgreSQL et REST confirment le même résultat.

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
- La CI utilise le service éphémère `pgvector/pgvector:pg17`, applique les migrations puis exécute ces intégrations dans une étape isolée.
- PR3 #38 : CI GitHub Backend Python, Frontend Svelte et GitGuardian toutes réussies sur le commit `06c5d70`.
- PR4 : Prettier valide le YAML du workflow manuel et le runbook; le build Docker MCP a réussi avec un contexte isolé de 1,06 Mo excluant `pgdata/`. L’image importe `serveur_mcp`; le smoke local contre PostgreSQL de test a vérifié `/healthz` et un refus HTTP 401 sur `/mcp` sans bearer. Le conteneur jetable a été arrêté; aucun service Clever Cloud n’a été modifié.
- PR #36–#39 : les checks Backend Python, Frontend Svelte et GitGuardian sont tous verts sur les derniers commits des quatre drafts; Sol a accepté chaque lot. Les drafts restent empilés et aucune fusion n’a eu lieu.
- Recette Claude Desktop locale du 2026-10-19 : la source synthétique confirmée BizDev `110` (produit `31`, révision `1`, empreinte `e787032ab3caaba783d4d4b1cc6bb396e09d86503c454064c614475771e02019`) a été lue par MCP; Claude a enregistré le rapport `28` avec la clé d’idempotence de recette. La base et la lecture paginée REST concordent : rapport courant, 1 087 caractères, titre `# Recette Claude Desktop RULA`, SHA-256 du Markdown `0bb02c2b1c384353e7762e39d0f132bc625bf75d79b649c539eb5b44a97075cf`. Aucun contenu de transcript ni de rapport n’est recopié ici. Détails synthétiques ignorés par Git : `D:\RULA-mcp-integration-20261019\.harness\rapports\claude-desktop-2026-10-19.md`.
- Vérification d’encodage limitée à la source synthétique `110` : le champ `transcripts.contenu` contient 80 caractères / 82 octets UTF-8 et deux U+02C6; la lecture REST assemble le contexte et le transcript en 110 caractères et restitue les mêmes deux U+02C6. Les accents sont donc déjà altérés dans la valeur persistée, avant le transport MCP; le serveur n’a pas créé cette différence. La cause exacte dans le script d’injection initial n’est pas établie. Aucune donnée ni aucun code n’a été corrigé; ne pas réécrire l’historique de recette.
- Le test Claude Desktop prouve le compte actuellement connecté et le transport stdio local seulement. Il ne prouve ni un compte Claude Pro individuel distinct, ni l’accès distant HTTP, ni un déploiement Clever Cloud.
- `bash scripts/harness.sh audit` : non requis.
- Tests d’intégration PostgreSQL exécutés uniquement sur la base dédiée du worktree; identité `rula_mcp_test|rula_test|5432`, tables initialement vides, extension `vector` disponible.

## Décisions

- ADR associée : [0004 — Rapports Claude et accès MCP](../../adr/0004-rapports-claude-mcp.md).
- Ordre des PR : `feature/rapports-claude` → `feature/mcp-transcripts` → `feature/parcours-rapports-claude` → `ops/deploiement-mcp-clever`. Aucune fusion ni exécution de déploiement n’est incluse.

## Handoff

- État de livraison : drafts #36 (`feature/rapports-claude`) → #37 (`feature/mcp-transcripts`) → #38 (`feature/parcours-rapports-claude`) → #39 (`ops/deploiement-mcp-clever`); quatre CI vertes et quatre acceptations Sol. Les PR restent en draft, sans fusion ni déploiement. Le transport stdio local est configuré dans Claude Desktop sous `rula-integration`; cette entrée et la base PostgreSQL de test sont conservées pour permettre de rejouer la recette.
- PR2 expose `python -m serveur_mcp` en stdio et `serveur_mcp:app` en HTTP `/mcp`; `/healthz` est public, les autres chemins exigent un bearer constant-time, et chaque transport vérifie en lecture seule les colonnes nécessaires avant de servir. Aucun transport ne lance de migration.
- Prochaines étapes humaines : fusionner #36, puis restacker et revérifier #37, #38 et #39 dans cet ordre; après fusion, appliquer la migration `002` au schéma cible autorisé, créer et protéger le bearer distant, configurer son secret avant de déployer l’application MCP dédiée, puis valider le transport HTTP et la persistance après redémarrage. Terminer par une recette depuis un second compte Claude individuel. Aucun de ces actes n’a été exécuté.
- Limites : la configuration locale `rula-integration` et la base de test sont conservées. Le POC local n’ajoute pas d’authentification applicative à RULA; l’accès distant dépend de la protection documentée. La corruption d’accents observée concerne uniquement les données synthétiques de cette recette et reste sans correctif.

## Revue indépendante

- Diff examiné : mise à jour de l’état des PR, des preuves Claude Desktop et du handoff.
- Critères vérifiés : CI #36–#39 vertes, acceptations Sol, rapport `28` courant et identique entre PostgreSQL et REST.
- Remarques : recette locale stdio uniquement; source synthétique `110` déjà mal encodée dans PostgreSQL.
- Verdict : mise à jour factuelle de la fiche; les étapes de fusion et de validation cloud restent humaines.
