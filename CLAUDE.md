# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Sobriété du code

Écrire le moins de lignes possible. Chaque ligne doit justifier son existence.

- Pas de commentaires ni de docstrings — jamais. Les noms doivent suffire.
- Pas de variables intermédiaires inutiles — chaîner directement.
- Pas d'abstractions prématurées : trois lignes similaires valent mieux qu'une abstraction injustifiée.
- Pas de gestion d'erreurs défensive sur des cas impossibles.
- Préférer les expressions aux blocs : comprehensions, expressions conditionnelles, `next()`, `any()`, `all()`.
- Un fichier court et dense vaut mieux qu'un fichier long et verbeux.

## Commandes essentielles

```bash
# Démarrage
docker compose up --build

# Backend — depuis la racine
uv run ruff check src/ tests/      # linter (bloquant)
uv run ruff format src/ tests/     # formatage
uv run mypy                        # type checking (bloquant)
uv run pytest                      # tests + couverture 100 % (bloquant) — ne pas utiliser pytest directement

# Frontend — depuis ui/
pnpm lint:check                    # ESLint
pnpm format:check                  # Prettier
pnpm svelte:check                  # Svelte + TypeScript
pnpm test                          # vitest
```

**Règle absolue :** les quatre contrôles backend (`ruff check`, `mypy`, `pytest`) et les trois contrôles frontend (`lint:check`, `format:check`, `svelte:check`) doivent passer à zéro erreur avant tout commit.

## Règle d'or des tests — zéro mock

**Il est interdit d'utiliser `MagicMock`, `Mock`, `patch`, `monkeypatch` ou tout mécanisme de monkey-patching.**

Les dépendances extérieures sont remplacées par des **classes `DeTest`** qui implémentent la même interface (ABC).

### Structure des doubles de test

```
src/adaptateurs/albert.py          → AdaptateurAlbert (ABC) + AdaptateurAlbertReel
tests/adaptateurs/albert_de_test.py → AdaptateurAlbertDeTest(AdaptateurAlbert)
```

Convention de nommage (identique au projet MQC) :
- Interface : `AdaptateurXxx` (ABC dans `src/`)
- Implémentation réelle : `AdaptateurXxxReel` (dans `src/`)
- Double de test : `AdaptateurXxxDeTest` (dans `tests/adaptateurs/` ou `tests/infra/`)
- Dépôt en mémoire : `DepotXxxMemoire` (dans `src/infra/memoire/` ou `tests/`)

### Injection par constructeur

Les services reçoivent leurs dépendances via le constructeur — jamais via un registre global ni une factory cachée :

```python
# ✅ correct
service = ServiceAnalyse(
    depot_transcripts=DepotTranscriptsMemoire(),
    albert=AdaptateurAlbertDeTest().avec_reponse('{"meta_features": []}'),
)

# ❌ interdit
with patch("service.albert") as mock_albert:
    ...
```

### Double de test avec builder fluent

```python
class AdaptateurAlbertDeTest(AdaptateurAlbert):
    def __init__(self) -> None:
        self._reponse = "{}"
        self.messages_recus: list[list[dict[str, str]]] = []

    def avec_reponse(self, reponse: str) -> "AdaptateurAlbertDeTest":
        self._reponse = reponse
        return self

    def completer(self, messages: list[dict[str, str]]) -> str:
        self.messages_recus.append(messages)
        return self._reponse
```

### Ce qui est exclu de la couverture (infrastructure)

Les adaptateurs réels qui nécessitent une ressource externe (DB, API) ne sont pas testés en unitaire :
- `src/infra/connexion_base_de_donnees.py` → omis du coverage (psycopg2 réel)
- Méthode `AdaptateurAlbertReel.completer` → `# pragma: no cover` (appels Albert réels)

Ces composants sont validés par des tests d'intégration ou manuellement.

## Architecture

Trois services Docker : `postgres` (17-alpine, init via `migrations/*.sql`), `backend` (FastAPI, port 3001), `frontend` (Svelte 5 + Vite, port 5173, proxy `/api` → backend).

### Backend (`src/`)

**Pattern de configuration** : toute lecture d'environnement passe par `charge_configuration()` dans `configuration.py`. Ne jamais lire `os.environ` directement ailleurs.

**Pattern de base de données** : le décorateur `@avec_connexion` dans `infra/connexion_base_de_donnees.py` gère le cycle de vie psycopg2. Toute méthode de dépôt PostgreSQL doit l'utiliser. Les tests utilisent un `DepotXxxMemoire` à la place.

**Appels LLM** : `AdaptateurAlbert` (ABC) dans `adaptateurs/albert.py` est l'interface unique vers Albert. `AdaptateurAlbertReel` est l'implémentation production. Les tests utilisent `AdaptateurAlbertDeTest`.

**Convention de nommage** : français partout (variables, fonctions, modules), cohérent avec le projet MQC.

### Frontend (`ui/src/`)

Svelte 5 avec la syntaxe runes (`$state`, `$derived`, `$effect`). Le proxy Vite redirige `/api/*` vers `http://backend:3001` — pas de CORS à gérer en dev.

## Schéma de données

`produits` → `transcripts` (N:1) et `analyses` (N:1) → `meta_features` (N:1). Les `verbatims` dans `meta_features` sont en `JSONB`.
