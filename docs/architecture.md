# Architecture technique RULA — POC

> **RULA** : Research User Listening & Analysis
> **Date** : 2026-06-16
> **Statut** : POC local — aucune exposition externe sans authentification

---

## Vue d'ensemble

```
┌─────────────┐    HTTP /api    ┌──────────────────┐    SQL      ┌──────────────┐
│  Svelte 5   │ ─────────────► │   FastAPI 3.13   │ ──────────► │ PostgreSQL17 │
│  Vite 6     │                │   uvicorn        │             │              │
│  port 5173  │                │   port 3001      │             │  port 5432   │
└─────────────┘                └──────────────────┘             └──────────────┘
                                        │
                                        │ HTTPS (Albert API)
                                        ▼
                               ┌──────────────────┐
                               │   Albert API     │
                               │  (LLM ANSSI)     │
                               └──────────────────┘
```

Trois services Docker orchestrés par `docker-compose.yml`. En développement, les sources Python et Svelte sont montées en volume pour le hot-reload.

---

## Stack technique

| Couche | Technologie | Version | Rôle |
|---|---|---|---|
| Langage backend | Python | 3.13 | — |
| Framework API | FastAPI + uvicorn | latest | REST API |
| Gestionnaire paquets Python | uv | — | Venv + dépendances |
| Base de données | PostgreSQL | 17-alpine | Stockage |
| Driver DB | psycopg2-binary | — | SQL brut (pas d'ORM) |
| LLM | Albert API | — | Extraction Meta-Features |
| Client HTTP | httpx | — | Appels Albert |
| Rate limiting | slowapi | — | Protection API |
| Langage frontend | TypeScript | 5.x | — |
| Framework frontend | Svelte | 5.x | UI |
| Bundler | Vite | 6.x | Dev server + build |
| Tests frontend | vitest | 3.x | Unit tests |
| Linter Python | ruff | — | Style + imports |
| Typage Python | mypy | — | Type checking |
| Linter frontend | ESLint | 9.x (flat config) | Style |
| Formatter frontend | Prettier + plugin-svelte | 3.x | Formatage |
| Conteneurisation | Docker + Compose | — | Orchestration locale |

**Décisions de design :**
- SQL brut via psycopg2 (pas d'ORM) : cohérence avec MQC, moins de magie, migrations explicites.
- Albert API plutôt qu'OpenAI : API compatible OpenAI, hébergement souverain ANSSI.
- Pas d'auth pour le POC : local uniquement, ProConnect prévu si POC concluant.

---

## Services Docker

### `postgres`
- Image : `postgres:17-alpine`
- Init automatique : les fichiers `migrations/*.sql` sont montés dans `/docker-entrypoint-initdb.d`
- Volume persistant : `postgres_data`
- Health check : `pg_isready` avant de démarrer le backend

### `backend`
- Build depuis `Dockerfile` (racine)
- Source montée : `./src:/app/src` (hot-reload en dev)
- Dépend de `postgres` (condition : healthy)
- Port : `3001`

### `frontend`
- Build depuis `ui/Dockerfile`
- Source montée : `./ui:/usr/src/app` (hot-reload Vite)
- Proxy `/api` → `http://backend:3001` (configuré dans `vite.config.ts`)
- Port : `5173`

---

## Structure du projet

```
RULA/
├── docs/
│   ├── technique.md           # Cadrage POC (hypothèse, critères, périmètre)
│   └── architecture.md        # Ce fichier
├── migrations/
│   └── 001_init.sql           # Schéma initial
├── src/                       # Backend Python
│   ├── serveur.py             # FastAPI app factory + point d'entrée uvicorn
│   ├── configuration.py       # Chargement config depuis env (NamedTuples)
│   ├── api/
│   │   └── api.py             # Router principal /api
│   ├── adaptateurs/
│   │   └── albert.py          # Client Albert API (httpx)
│   └── infra/
│       └── connexion_base_de_donnees.py  # Décorateur psycopg2
├── tests/                     # Tests pytest
├── ui/                        # Frontend Svelte
│   ├── src/
│   │   ├── App.svelte
│   │   └── main.ts
│   ├── index.html
│   ├── vite.config.ts
│   ├── svelte.config.js
│   ├── tsconfig.json
│   ├── package.json
│   ├── eslint.config.js
│   └── .prettierrc
├── docker-compose.yml
├── Dockerfile                 # Backend
├── pyproject.toml
├── .env.template
├── .dockerignore
└── .gitignore
```

---

## Schéma de base de données

```sql
produits (id, nom, cree_le)
    │
    ├── transcripts (id, titre, contenu, produit_id, date_entretien, cree_le, modifie_le)
    │
    └── analyses (id, produit_id, date_debut, date_fin, cree_le)
            │
            └── meta_features (id, analyse_id, nom, description, occurrences, verbatims)
```

`verbatims` est stocké en `JSONB` : liste des extraits textuels sources de la Meta-Feature.

---

## Flux d'analyse LLM

```
1. POST /api/analyses
   { produit_id, date_debut, date_fin }
        │
        ▼
2. Récupère tous les transcripts du produit sur la période
        │
        ▼
3. Construit un prompt avec le corpus complet
        │
        ▼
4. POST Albert API /v1/chat/completions
   → Retourne JSON : liste de Meta-Features avec occurrences + verbatims
        │
        ▼
5. Stocke en base : INSERT analyses + meta_features
        │
        ▼
6. GET /api/analyses/{id}/meta-features → UI affiche les résultats
```

**Format de réponse Albert attendu (JSON strict) :**
```json
{
  "meta_features": [
    {
      "nom": "Difficulté de navigation",
      "description": "Les utilisateurs peinent à trouver les guides thématiques",
      "occurrences": 4,
      "verbatims": ["je ne trouve pas...", "c'est pas clair..."]
    }
  ]
}
```

---

## Harness de linting

### Backend
```bash
# Linting
uv run ruff check src/ tests/

# Formatage
uv run ruff format src/ tests/

# Type checking
uv run mypy
```

### Frontend
```bash
cd ui

# Linting
pnpm lint:check        # ESLint
pnpm format:check      # Prettier
pnpm svelte:check      # svelte-check + TypeScript

# Auto-fix
pnpm lint:fix
pnpm format:fix
```

### Lancer les tests
```bash
# Backend
uv run pytest

# Frontend
cd ui && pnpm test
```

---

## Démarrage en développement

```bash
# 1. Copier et remplir les variables d'environnement
cp .env.template .env

# 2. Lancer l'ensemble
docker compose up

# Frontend : http://localhost:5173
# Backend  : http://localhost:3001
# API docs : http://localhost:3001/docs
```

---

## Variables d'environnement

| Variable | Description | Défaut |
|---|---|---|
| `ALBERT_URL` | URL de l'API Albert | — |
| `ALBERT_CLE_API` | Clé d'authentification Albert | — |
| `ALBERT_MODELE` | Modèle LLM à utiliser | `openweight-medium` |
| `DB_HOTE` | Hôte PostgreSQL | `localhost` |
| `DB_PORT` | Port PostgreSQL | `5432` |
| `DB_NOM` | Nom de la base | `rula` |
| `DB_UTILISATEUR` | Utilisateur PostgreSQL | `rula` |
| `DB_MOT_DE_PASSE` | Mot de passe PostgreSQL | — |
| `RULA_PORT` | Port du backend | `3001` |
| `RULA_MAX_REQUETES_PAR_MINUTE` | Limite de rate limiting | `100` |
