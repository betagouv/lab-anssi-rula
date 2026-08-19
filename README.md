# RULA

Un outil de centralisation et d'analyse des transcripts d'entretiens utilisateurs, basé sur [Albert](https://github.com/betagouv/albert-api).

## 📦 Comment installer ?

Il faut installer `python`, `uv`, `pnpm` et `docker`.

```bash
cp .env.template .env   # puis remplir les variables
uv sync
cd ui && pnpm install
```

## 🚀 Comment démarrer ?

```bash
docker compose up --build
```

- Frontend : http://localhost:5173
- Backend  : http://localhost:3001
- API docs : http://localhost:3001/docs

Si le volume PostgreSQL existe déjà lorsqu'une nouvelle migration est ajoutée,
les scripts d'initialisation Docker ne sont pas rejoués automatiquement. Pour
appliquer les migrations `012` à `014` du POC sur une base locale existante :

```bash
docker compose exec -T postgres psql -U rula -d rula \
  -f /docker-entrypoint-initdb.d/012_besoins_detectes.sql
docker compose exec -T postgres psql -U rula -d rula \
  -f /docker-entrypoint-initdb.d/013_nettoyage_exports.sql
docker compose exec -T postgres psql -U rula -d rula \
  -f /docker-entrypoint-initdb.d/014_sources_brutes_correspondances.sql
```

## ⚙️ Variables d'environnement

Créer un fichier `.env` à partir de `.env.template`.

| Variable | Description |
|---|---|
| `ALBERT_URL` | URL de l'API Albert |
| `ALBERT_CLE_API` | Clé d'authentification Albert |
| `ALBERT_MODELE` | Modèle LLM (défaut : `openweight-medium`) |
| `DB_MOT_DE_PASSE` | Mot de passe PostgreSQL |
| `RULA_HTTP_BASIC_AUTH` | Identifiants de démo au format `utilisateur:mot_de_passe` |

## 🧪 Comment valider ?

```bash
# Backend
uv run ruff check src/ tests/
uv run mypy
uv run pytest

# Frontend
cd ui
pnpm lint:check
pnpm format:check
pnpm svelte:check
```

## ☁️ Déploiement DÉMO

Le déploiement sur Clever Cloud et sa configuration sont documentés dans
[la procédure dédiée](docs/deploiement-clever-cloud.md).
