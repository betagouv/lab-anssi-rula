# RULA

Un outil de centralisation et d'analyse des transcripts d'entretiens utilisateurs, basé sur [Albert](https://github.com/betagouv/albert-api).

## 📦 Comment installer ?

Il faut installer `python`, `uv`, `pnpm`, `bash` et `docker`.

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

## 🤖 Assistance au développement par LLM

Le harness local peut être complété par [Serena](https://github.com/oraios/serena),
un serveur MCP open source sous licence MIT. Il donne aux agents une navigation
sémantique du code (symboles, références et diagnostics) ; il ne remplace ni la
revue humaine ni les contrôles `scripts/harness.sh`.

Serena s'exécute localement via `uvx`, sans installation globale. Sa configuration
MCP est propre au poste et l'index du projet est conservé dans `.serena/`, ignoré
par Git. L'installation télécharge ses dépendances depuis GitHub et les serveurs de
langage nécessaires ; Serena n'envoie volontairement aucun code du dépôt à un
service distant.

Depuis la racine du dépôt, initialiser puis indexer RULA :

```powershell
uvx --from git+https://github.com/oraios/serena serena-agent.exe init
uvx --from git+https://github.com/oraios/serena serena-agent.exe project index . --language python --language svelte
```

Pour enregistrer Serena dans Codex :

```powershell
codex mcp add serena -- uvx --from git+https://github.com/oraios/serena serena-agent.exe start-mcp-server --context=codex --project-from-cwd
```

Pour Claude Code sous Windows, le passage par `cmd.exe` préserve les options de
`uvx` :

```powershell
claude mcp add --scope user serena -- cmd.exe /d /s /c "uvx --from git+https://github.com/oraios/serena serena-agent.exe start-mcp-server --context=claude-code --project-from-cwd"
```

Vérifier les deux configurations avec `codex mcp list` et `claude mcp list`. Pour
contrôler l'index sur Windows, utiliser une sortie UTF-8 :

```powershell
$env:PYTHONIOENCODING = "utf-8"
uvx --from git+https://github.com/oraios/serena serena-agent.exe project health-check .
```

Les commandes `codex mcp add` et `claude mcp add` ajoutent une configuration
utilisateur : elles s'appliquent donc aux futurs projets ouverts avec ces clients,
mais `--project-from-cwd` active uniquement le dépôt courant. Redémarrer le client
ou ouvrir une nouvelle session après la configuration pour voir les outils MCP.

## ☁️ Déploiement DÉMO

Le déploiement sur Clever Cloud et sa configuration sont documentés dans
[la procédure dédiée](docs/deploiement-clever-cloud.md).
