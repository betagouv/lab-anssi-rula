# CLAUDE.md — Backend

## Règle d'or : zéro mock dans les tests

Ne jamais utiliser `MagicMock`, `Mock` ou `patch`. Toute dépendance externe a une classe `DeTest` dans `tests/`.

## Patterns obligatoires

### Configuration
```python
from configuration import charge_configuration
config = charge_configuration()   # ✅
os.environ.get("ALBERT_URL")      # ❌ jamais directement
```

### Interfaces et doubles de test

Chaque adaptateur externe suit ce schéma :

```
src/adaptateurs/xxx.py
├── class AdaptateurXxx(ABC)          # interface — utilisée partout comme type
├── class AdaptateurXxxReel(...)      # implémentation prod
│   └── def methode(self) -> ...:    # pragma: no cover  ← appels réseau/DB réels

tests/adaptateurs/xxx_de_test.py
└── class AdaptateurXxxDeTest(AdaptateurXxx)   # double de test — builder fluent
    ├── messages_recus: list[...]               # état observable
    └── def avec_reponse(self, r) -> Self       # configuration du comportement
```

### Dépôts base de données

```python
from infra.connexion_base_de_donnees import avec_connexion

class DepotTranscriptsPostgres:
    def __init__(self, config: BaseDeDonnees) -> None:
        self._config = config
        self._connexion: Any = None   # injecté par le décorateur

    @avec_connexion
    def lister(self) -> list[dict]:   # pragma: no cover
        with self._connexion.cursor() as cur:
            cur.execute("SELECT * FROM transcripts")
            return cur.fetchall()
```

Les tests utilisent `DepotTranscriptsMemoire` (dans `src/infra/memoire/`) à la place.

### Appels Albert

```python
# Production
albert: AdaptateurAlbert = AdaptateurAlbertReel(config.albert)

# Tests
albert: AdaptateurAlbert = (
    AdaptateurAlbertDeTest()
    .avec_reponse('{"meta_features": [{"nom": "Accès difficile", "occurrences": 3}]}')
)
resultat = json.loads(albert.completer([{"role": "user", "content": corpus}]))
```

## Structure des routes FastAPI

Chaque domaine métier a son propre `APIRouter` dans `api/`. Le routeur est enregistré dans `serveur.py` avec un préfixe `/api`.

## Typage

Tous les types doivent être explicites (mypy strict). Utiliser `NamedTuple` pour les structures de données internes, `pydantic.BaseModel` pour les corps de requêtes FastAPI.
