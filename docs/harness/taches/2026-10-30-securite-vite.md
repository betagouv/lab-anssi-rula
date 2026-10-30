# Tâche : corriger la version vulnérable de Vite

Statut : prête à revoir

## Objectif

Résoudre les avis de sécurité affectant Vite 6.4.3 en utilisant la première version corrigée qui ferme les avis connus, sans élargir la mise à jour aux autres dépendances.

## Périmètre

- Inclus : `ui/package.json`, `ui/pnpm-lock.yaml`, preuves et suivi de cette tâche.
- Exclu : autres vulnérabilités de l’audit, changements de configuration d’exposition réseau, déploiement et fusion.

## Critères d’acceptation

- [x] Le manifeste demande Vite `^6.4.5` et le lock résout tous les chemins Vite à `6.4.5`.
- [x] Les autres dépendances directes et transitives restent inchangées.
- [x] Installation frozen, `pnpm why vite`, audit ciblé et validations Vite/proxy/filesystem sont documentés.
- [x] Aucun avis Vite connu des GHSA ciblés ne reste; les autres avis ne sont pas présentés comme résolus.

## Plan

1. Vérifier l’état du lock et les chemins de dépendances Vite avant modification.
2. Mettre à jour le manifeste et régénérer le lock avec pnpm sans changer les autres versions résolues.
3. Installer en mode frozen et examiner les dépendances et l’audit.
4. Valider le démarrage Svelte et le proxy `/api`, puis les variantes d’accès au filesystem sur fixtures synthétiques sous Linux isolé.
5. Exécuter les contrôles requis, documenter leurs résultats et soumettre le diff pour revue avant commit.

## Validation

- `corepack pnpm --dir ui install --frozen-lockfile` : réussi; `pnpm why vite` ne montre que Vite 6.4.5 dans les chemins directs, Svelte, Vitest, `vite-node`, `@vitest/mocker`, inspector et `vitefu`.
- `corepack pnpm --dir ui test`, `check`, `lint:check`, `format:check`, `build` : tous réussis sous Windows; 38 tests frontend réussis, Svelte sans erreurs ni avertissements, build Vite 6.4.5.
- `corepack pnpm --dir ui audit --json` : avant 3 faibles, 13 modérés, 22 élevés, 2 critiques; après 2 faibles, 10 modérés, 21 élevés, 2 critiques. Aucun avis restant sur le module `vite`. Les alertes restantes concernent `@vitest/mocker`, `brace-expansion`, `deepmerge`, `devalue`, `js-yaml`, `nanoid`, `postcss`, `postcss-selector-parser`, `source-map-js`, `tinypool` et `vitest`; elles restent hors périmètre.
- Fixtures synthétiques dans un conteneur Linux Node 24.22.2 avec Vite 6.4.5 : un fichier public autorisé hors racine est servi (200), `.env` sous `server.fs.allow` est refusé avec `?raw`, `?import&raw` et `?import&url&inline` (403), et un leurre de projet `etc/hostname` importé ne permet pas de lire `/@fs/etc/hostname` (403). Seul le texte synthétique est utilisé.
- App RULA dans un conteneur Linux isolé : `/` et `/src/main.ts` retournent 200; `/api/__vite_proxy_probe` reçoit la réponse du faux backend; le handshake WebSocket `vite-hmr` renvoie `{"type":"connected"}`.
- `bash scripts/harness.sh complet` : réussi avec `NODE_OPTIONS=--experimental-global-webcrypto` transmis à WSL via `WSLENV=NODE_OPTIONS/u`; Node exécuté par pnpm : `v24.13.0`. Backend : Ruff et mypy réussis, 122 tests réussis et 4 migrations ignorées. Frontend : 38 tests, check, lint, format et build réussis.
- `git diff --check` : réussi.
- `bash scripts/harness.sh audit` (Qlty local) : non exécuté, non requis pour cette mise à jour de dépendance.

## Décisions

- ADR associée ou « aucune » : aucune.
- Version cible : Vite `^6.4.5`, car les avis connus touchent jusqu’à 6.4.4 inclus.
- [GHSA-rq7h-c2jc-7f22](https://github.com/advisories/GHSA-rq7h-c2jc-7f22) exige un serveur exposé au réseau et une collision entre import relatif et chemin système sous Linux; cette collision n’est pas établie dans RULA. [GHSA-9jrq-w75r-8gcw](https://github.com/advisories/GHSA-9jrq-w75r-8gcw) concerne un middleware Vite personnalisé absent de la configuration RULA. [GHSA-8g5g-mxqh-grgj](https://github.com/advisories/GHSA-8g5g-mxqh-grgj) réintroduit en 6.4.4 un contournement de `server.fs.deny` par paramètres de requête, corrigé en 6.4.5.
- Aucun élément ne prouve une compromission ou l’exploitation de ces cas dans RULA.

## Handoff

- État du code : base `ee161edeb1f5060c26eb6242480b5fe3fef5925a`, branche `fix/vite-securite`; seuls le manifeste, le lock et cette fiche diffèrent.
- Prochaine action : revue finale du diff et des preuves avant commit/PR.
- Risques ou limites : `vite.config.ts` écoute sur toutes les interfaces et Docker publie le port; l’accessibilité externe et l’exploitation ne sont pas établies. L’audit comporte d’autres avis hors de cette tâche.

## Revue indépendante

- Diff examiné : bump du manifeste et résolutions Vite du lock; aucune autre version ne change.
- Critères vérifiés : branche Vite homogène en 6.4.5, audit sans avis Vite, validations frontend/backend et scénarios filesystem/proxy/HMR exécutés.
- Remarques : la configuration `host: true` est inchangée; cette tâche ne démontre pas l’accessibilité externe ou l’exploitation du serveur courant. L’audit garde les alertes hors périmètre indiquées plus haut.
- Verdict : ACCEPTE — revue indépendante Sol du code, des preuves et de la fiche finale.
