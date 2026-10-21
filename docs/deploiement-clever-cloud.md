# Déploiement DÉMO sur Clever Cloud

RULA est déployé comme une application Python unique : FastAPI sert l'API et
le frontend Svelte compilé. Le hook post-build exécute les migrations avant le
démarrage du runtime; la migration de recentrage des données doit donc être
coordonnée avec l’exploitation.

## Ressources Clever Cloud

Conserver la base PostgreSQL active déjà liée à l’application Python
`lab-anssi-rula-demo` dans l’organisation `ANSSI-DEMO`. La migration doit
préserver les transcripts confirmés MSS/MSC sur cette base; ne pas remplacer
la base par une nouvelle base vide. Clever Cloud injecte les variables
`POSTGRESQL_ADDON_*`, utilisées automatiquement par RULA.

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

## Bascule vers la pseudonymisation seule

La migration `002_pseudonymisation_seule.sql` conserve les produits MSS et MSC
et les seules lignes `transcripts` qui satisfont simultanément les conditions
suivantes : `confirme = TRUE`, `type_source IN ('produit', 'bizdev')` et
rattachement à l’un des deux produits. Les identifiants des lignes conservées
sont préservés. Elle supprime les autres tables applicatives, dont les données
d’analyse, projets, FeatureBase et imports BizDev tabulaires.

Cette migration est destructive et le hook la joue avant le lancement du
nouveau runtime. Ne lancer le build sur la base active qu’après avoir planifié
une fenêtre de maintenance, arrêté toutes les anciennes instances et réalisé
la sauvegarde opérationnelle applicable. Les sauvegardes Clever Cloud ne sont
pas modifiées. Après le build, vérifier `migrations_executees`, la présence de
MSS et MSC, les sources confirmées attendues et `GET /api/sante`. Si le hook
échoue, garder les instances arrêtées et restaurer la sauvegarde; ne pas
relancer le nouveau runtime sur une base partiellement migrée. Le SQL est
transactionnel avec le runner : une erreur avant validation annule le schéma
et les suppressions de cette migration.

Sur une base vide, le runner exécute d’abord `001_schema_unifie.sql`, puis
`002_pseudonymisation_seule.sql`; le schéma initial est conservé pour les
installations existantes et pour reconstruire le chemin de migration. La
réexécution via le runner est ignorée grâce à `migrations_executees`.

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

Le workflow **Déploiement DÉMO** est volontairement manuel. La présente PR ne
demande pas de lancement de ce workflow. Le lancer depuis
la branche `main` dans l'onglet Actions ; toute autre branche est refusée.

Après le premier déploiement, vérifier l'authentification HTTP, la page
d'accueil, `GET /api/sante`, le journal Clever Cloud et l'enregistrement des
migrations. Relancer le workflow pour vérifier qu'aucune migration n'est
rejouée.

Le backend omet ses lignes d'accès pour les réponses réussies du suivi de
préparation PDF. Les journaux d'accès du proxy Clever Cloud restent gérés par
la plateforme et ne sont pas filtrés par l'application.
