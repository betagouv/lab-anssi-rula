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

## ⚙️ Variables d'environnement

Créer un fichier `.env` à partir de `.env.template`.

| Variable | Description |
|---|---|
| `ALBERT_URL` | URL de l'API Albert |
| `ALBERT_CLE_API` | Clé d'authentification Albert |
| `ALBERT_MODELE` | Modèle LLM (défaut : `openweight-medium`) |
| `DB_MOT_DE_PASSE` | Mot de passe PostgreSQL |

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
