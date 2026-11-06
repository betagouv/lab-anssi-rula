# Tâche : lier les ports Docker de développement à 127.0.0.1

Statut : prête à revoir

## Objectif

Empêcher l'accès réseau au serveur de dev Vite (5173), à l'API (3001) et à PostgreSQL (5432) publiés par `docker-compose.yml`, signalé en revue (`server.host: true` + port publié sur toutes les interfaces).

## Périmètre

- Inclus : les trois publications de ports de `docker-compose.yml`, `README.md`, `docs/architecture.md`.
- Exclu : `ui/vite.config.ts` et `ui/Dockerfile` (`host: true` est nécessaire dans le conteneur), déploiement, fusion.

## Critères d'acceptation

- [x] `docker compose ps` affiche `127.0.0.1:5173->5173`, `127.0.0.1:3001->3001`, `127.0.0.1:5432->5432`.
- [x] `http://localhost:5173` charge l'UI et `/api/*` répond.
- [x] Une connexion via l'IP LAN de l'hôte sur ces ports est refusée.

## Plan

1. Préfixer les ports par `127.0.0.1` dans `docker-compose.yml`.
2. Documenter la restriction et sa levée volontaire.
3. Vérifier la configuration compose et l'accessibilité.

## Validation

- Commandes ciblées pendant l'itération : `docker compose config`
- Runtime (`docker compose up --build`) : ports affichés en `127.0.0.1`; `localhost:5173` et `/api` via proxy répondent 200; connexions refusées sur `192.168.1.54` (IP Wi-Fi) pour 5173, 3001 et 5432.
- `bash scripts/harness.sh complet` : non exécuté (changement de configuration Docker et documentation uniquement)
- `bash scripts/harness.sh audit` : non requis

## Décisions

- ADR associée ou « aucune » : aucune.
- Suite de la tâche `2026-10-30-securite-vite.md`, qui avait exclu l'exposition réseau.

## Handoff

- État du code : branche `fix/exposition-ports-locale` depuis `origin/main`.
- Prochaine action : vérification runtime puis revue.
- Risques ou limites : un accès distant légitime en dev nécessitera un `docker-compose.override.yml`.

## Revue indépendante

- Diff examiné :
- Critères vérifiés :
- Remarques :
- Verdict :
