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
| LLM | Albert API | — | Analyse de transcripts |
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
│   │   ├── navigation/        # Navigation principale et routage par hash
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

## Organisation fonctionnelle de l'IHM

L'interface est organisée selon le parcours métier suivant :

```text
Sources → Analyse transverse du produit
```

### Données sources

- **Entretiens utilisateurs** : transcripts saisis ou importés dans RULA.
- **Retours BizDev** : retours importés depuis un export CSV BizDev.
- **Demandes FeatureBase** : demandes importées depuis FeatureBase via un export CSV.

Les trois sources sont accessibles depuis un produit. Les transcripts sont
rattachés à un projet ; les retours BizDev et les demandes FeatureBase sont
transverses au produit et conservent `projet_id` à `NULL` pour les nouveaux
imports. Les routes historiques d'import restent compatibles avec les anciens
appels pouvant cibler un projet.

### Normalisation et analyse transverse

Le dashboard d'un produit propose une vue transverse unique :

Les traitements par source convergent dans `besoins_detectes`, puis les
correspondances regroupent les noms génériques. Chaque groupe expose les
passages bruts des transcripts, de FeatureBase et de BizDev, avec un lien vers
la source d'origine.

L'**historique des analyses** reste accessible depuis la page des entretiens.
Il s'agit d'un espace de suivi du traitement, et non d'un niveau principal de
navigation.

Le dashboard produit expose une analyse transverse unique. Elle normalise tous
les transcripts des projets du produit, les deux sources CSV du produit, puis
calcule les correspondances. Les besoins et correspondances sont isolés par
`produit_id` ; les anciennes API globales restent disponibles.

La navigation frontend utilise des hashes URL, notamment :

```text
#sources/entretiens
#sources/retours-bizdev
#sources/featurebase
#sources/retours-bizdev/123
#sources/featurebase/123
#analyses
```

Les transcripts consultables depuis une analyse transverse utilisent la route
projet-scopée `#projets/{projet_id}/entretiens/{entretien_id}`. Cette vue est en
lecture seule ; l'ancien détail global des transcripts n'est plus rendu.

Les anciennes API `/besoins` et `/correspondances` restent disponibles pour les
clients historiques, mais leurs vues globales ne sont plus proposées dans la
navigation frontend.

---

## Schéma de base de données

```sql
transcripts (id, titre, contenu, produit_id, date_entretien, cree_le, modifie_le)
    │
    └── analyses_transcripts (id, transcript_id, contenu, cree_le)
```

Chaque transcript ne possède qu'une analyse. `contenu` stocke la synthèse Markdown
générée par Albert.

---

## Flux d'analyse LLM

```
1. POST /api/analyses/transcripts/{transcript_id}
        │
        ▼
2. Récupère le transcript demandé
        │
        ▼
3. Envoie le prompt d'analyse et le contenu du transcript à Albert
        │
        ▼
4. POST Albert API /v1/chat/completions
   → Retourne une synthèse Markdown structurée
        │
        ▼
5. Stocke en base : INSERT analyses_transcripts
        │
        ▼
6. GET /api/analyses/transcripts/{transcript_id}
   → Retourne l'analyse associée au transcript
```

Le prompt impose une structure Markdown en dix sections (profil, compréhension
du sujet, besoins, points de douleur, cas concrets, contournements,
priorisation, questions ouvertes, vocabulaire et synthèse). Le résultat reste
consultable via `GET /api/analyses`.

## Parcours d’analyse par projet

Les projets de recherche disposent d’une copie modifiable des blocs de prompt du
produit : rôle, contextes produit/brief/projet, règles, consignes d’étape et
instructions de sortie. Albert reçoit ces blocs assemblés dans cet ordre, puis
les transcripts et les résultats validés des étapes précédentes comme données.

Le parcours comporte six étapes : import, configuration, scan neutre, points à
retenir, thématisation et consultation de l’analyse. Les trois étapes Albert
produisent un brouillon éditable et une version validée ; une étape ne peut pas
être générée avant la validation de la précédente. Le garde-fou s’applique
uniquement au contenu du transcript lors de son enregistrement.

La page d’un projet est un hub indépendant de cette progression. Elle regroupe
les transcripts, les retours BizDev, les demandes FeatureBase et les statuts des
étapes d’analyse. Les transcripts sont consultables via
`GET /api/projets/{projet_id}/entretiens/{entretien_id}` en lecture seule. Les
imports restent accessibles depuis le menu du projet et sont bornés au projet
courant.

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
