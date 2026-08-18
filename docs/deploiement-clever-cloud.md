# Déploiement DÉMO sur Clever Cloud

RULA est déployé comme une application Python unique : FastAPI sert l'API et
le frontend Svelte compilé. L'environnement DÉMO ne contient aucune reprise de
données locales.

## Ressources Clever Cloud

Dans l'organisation `ANSSI-DEMO`, créer une base PostgreSQL dédiée vide nommée
`lab-anssi-rula-demo-db`, puis une application Python nommée
`lab-anssi-rula-demo`. Lier la base à l'application : Clever Cloud injecte les
variables `POSTGRESQL_ADDON_*`, utilisées automatiquement par RULA.

Configurer les variables non secrètes suivantes dans l'application :

```text
CC_PYTHON_VERSION=3.13
CC_NODE_VERSION=24
CC_RUN_COMMAND=uv run --no-dev uvicorn serveur:app --host 0.0.0.0 --port 9000 --app-dir src
CC_POST_BUILD_HOOK=sh scripts/clever-cloud/post-build-clever.sh
CC_HEALTH_CHECK_PATH=/api/sante
RULA_HOTE=0.0.0.0
RULA_PORT=9000
```

Configurer exclusivement dans Clever Cloud les secrets `ALBERT_CLE_API` et
`CC_HTTP_BASIC_AUTH`, ainsi que `ALBERT_URL` et les options Albert nécessaires
à l'environnement. `CC_HTTP_BASIC_AUTH` protège l'interface et l'API avec la
valeur `utilisateur:mot_de_passe`.

Le hook de post-build compile l'interface puis exécute les migrations SQL. La
table `migrations_executees` empêche qu'une migration soit jouée deux fois.

## Déploiement GitHub Actions

Créer l'environnement GitHub `DEMO` et y définir les secrets suivants :

```text
CLEVER_CLOUD_TOKEN
CLEVER_CLOUD_SECRET
CLEVER_CLOUD_ID_APP
CLEVER_CLOUD_ID_ORGANISATION
```

Les deux premiers proviennent de Clever Tools et expirent annuellement. Les
secrets applicatifs et ceux de la base restent dans Clever Cloud, jamais dans
GitHub.

Le workflow **Déploiement DÉMO** est volontairement manuel. Le lancer depuis
la branche `main` dans l'onglet Actions ; toute autre branche est refusée.

Après le premier déploiement, vérifier l'authentification HTTP, la page
d'accueil, `GET /api/sante`, le journal Clever Cloud et l'enregistrement des
migrations. Relancer le workflow pour vérifier qu'aucune migration n'est
rejouée.
