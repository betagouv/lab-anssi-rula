# Règles de développement RULA

Ce fichier est le point d'entrée commun aux agents intervenant sur RULA. `CLAUDE.md` est un lien symbolique vers ce fichier pour conserver la compatibilité avec Claude Code. L'architecture détaillée reste dans [docs/architecture.md](docs/architecture.md) et la CI.

## Sobriété du code

Écrire le moins de lignes possible. Chaque ligne doit justifier son existence.

- Pas de commentaires ni de docstrings — jamais. Les noms doivent suffire.
- Pas de variables intermédiaires inutiles ni d'abstractions prématurées.
- Pas de gestion d'erreurs défensive sur des cas impossibles.
- Préférer les expressions aux blocs et les fichiers courts.

## Commandes essentielles

```bash
docker compose up --build
uv run ruff check src/ tests/
uv run ruff format src/ tests/
uv run mypy
uv run pytest
cd ui && pnpm lint:check && pnpm format:check && pnpm svelte:check && pnpm test
```

Les quatre contrôles backend (`ruff check`, `mypy`, `pytest`, couverture 100 %) et les contrôles frontend doivent passer avant tout commit.

## Tests

Les dépendances extérieures sont remplacées par des classes `DeTest` implémentant la même interface ABC. Les services reçoivent leurs dépendances par constructeur ; aucun mock ou monkey-patching n'est utilisé.

## Architecture

RULA utilise trois services Docker : `postgres`, `backend` FastAPI et `frontend` Svelte 5 + Vite. Toute configuration passe par `charge_configuration()` et toute méthode de dépôt PostgreSQL utilise `@avec_connexion`.

### Règle d'or des tests

Les doubles de test suivent les interfaces ABC et portent le suffixe `DeTest`. Les adaptateurs réels qui nécessitent une ressource externe ne sont pas couverts en unitaire ; ils sont validés par intégration ou manuellement.

### Backend (`src/`)

- Les appels LLM passent par `AdaptateurAlbert`, dont `AdaptateurAlbertReel` est l'implémentation de production.
- Les lectures d'environnement passent par `charge_configuration()`.
- Les dépôts PostgreSQL utilisent `@avec_connexion` ; les tests utilisent les dépôts mémoire.
- Les noms de variables, fonctions et modules sont en français.

### Frontend (`ui/src/`)

Svelte 5 utilise les runes (`$state`, `$derived`, `$effect`). Le proxy Vite redirige `/api/*` vers `http://backend:3001`.

## Schéma de données

`produits` → `transcripts` (N:1) et `analyses` (N:1) → `meta_features` (N:1). Les verbatims dans `meta_features` sont en `JSONB`.

## Démarrage d'une tâche

1. Lire le dépôt, l'historique récent et la fiche de tâche concernée dans `docs/harness/taches/`.
2. Vérifier `git status` et ne modifier qu'un worktree à la fois.
3. Reformuler les critères observables avant d'écrire du code.
4. Créer ou mettre à jour une fiche depuis `docs/harness/modeles/fiche-de-tache.md`.

Une branche décrit uniquement le changement, par exemple `feature/import-transcript` ou `fix/validation-api`. Elle ne contient pas le nom d'un agent, d'un outil ou d'un contributeur.

## Rôles

- Le planificateur précise le contrat de tâche et les critères d'acceptation.
- L'implémenteur est le seul rôle qui modifie le code de la tâche.
- Le relecteur lit le diff, la fiche et les preuves de validation. Il ne modifie pas le code ; il consigne des remarques actionnables dans la fiche.

La fusion d'une pull request est toujours décidée par un humain.

## Contrôles locaux

Depuis la racine :

```bash
bash scripts/harness.sh rapide --cible backend
bash scripts/harness.sh complet
bash scripts/harness.sh audit
```

`rapide` est utilisé pendant l'itération, avec les tests ciblés indiqués dans la fiche. `complet` est requis avant PR et reproduit les contrôles de la CI. `audit` produit des constats Qlty non bloquants dans `.harness/rapports/` ; il n'envoie rien à un service externe et n'applique jamais de correction.

Les diagnostics Qlty ne remplacent ni Ruff ni ESLint. Ils servent à suivre la complexité, la duplication et l'analyse Bandit hors tests.

## Navigation sémantique locale

[Serena](README.md#-assistance-au-développement-par-llm) est optionnel : il apporte aux agents des outils MCP locaux de navigation par symboles et références. Son index `.serena/` ne doit jamais être ajouté à Git ; son installation ne remplace aucune commande de contrôle du harness.

## Décisions et reprise

- Une décision durable est consignée dans `docs/adr/` depuis son modèle.
- Une fiche de tâche contient le contrat, les commandes exécutées, le handoff et la revue.
- Une tâche longue ou parallèle utilise son propre worktree. Ne jamais partager un worktree entre deux agents qui écrivent.
