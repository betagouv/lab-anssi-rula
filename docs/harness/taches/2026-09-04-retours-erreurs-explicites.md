# Tâche : Retours d’erreur explicites

Statut : prête à revoir

## Objectif

Retourner un message compréhensible lorsqu’Albert est indisponible, lorsqu’une
réponse distante est invalide ou lorsqu’un formulaire de transcript est
incomplet, sans persister de données invalides.

## Périmètre

- Inclus : branche `erreurs-explicites` depuis `main` synchronisé, exceptions
  Albert, réponses FastAPI `detail`, validation des transcripts, parseur frontend
  partagé, écrans MVP et tests.
- Exclu : migration de schéma, retry automatique, modification du format
  `{"detail": ...}` et fusion de la PR.

## Critères d’acceptation

- [x] Les erreurs timeout, réseau, HTTP et réponse invalide d’Albert sont
  converties en retours utilisateur explicites.
- [x] Le délai d’Albert est limité à 30 secondes.
- [x] Les champs transcript absents, vides ou composés d’espaces sont refusés
  avant tout appel à Albert et toute écriture.
- [x] Le frontend interprète les erreurs JSON, HTML, structurées et réseau sans
  afficher `Unexpected token '<'`.
- [x] Les retours `ProjetNonConforme` et `TranscriptNonConforme` restent
  spécialisés.
- [x] Les erreurs visibles des écrans MVP sont annoncées comme alertes
  accessibles.

## Plan

1. Ajouter la hiérarchie d’erreurs Albert et son adaptation HTTP.
2. Centraliser les erreurs FastAPI et valider les modèles avant les services.
3. Unifier les appels frontend et valider les formulaires MVP.
4. Ajouter les tests de non-régression, l’ADR et les preuves de contrôle.

## Validation

- Commandes ciblées pendant l’itération : `uv run pytest` (158 tests, couverture
  100 %), Ruff, mypy, svelte-check, ESLint, Prettier et Vitest (53 tests).
- `bash scripts/harness.sh complet` : backend validé ; étape frontend bloquée par
  la résolution de `pnpm.cmd` Windows dans Bash.
- `bash scripts/harness.sh audit` : exécuté ; rapports SARIF générés dans
  `.harness/rapports/`.

## Décisions

- ADR associée : [0002-erreurs-explicites](../../adr/0002-erreurs-explicites.md).

## Handoff

- État du code : implémentation terminée sur `erreurs-explicites`, sans
  changement de schéma.
- Prochaine action : faire relire la [PR #17](https://github.com/betagouv/lab-anssi-rula/pull/17).
- Risques ou limites : le contrôle frontend via `pnpm` est bloqué localement par
  l’autorisation de build `esbuild`; les binaires installés ont été contrôlés
  directement.

## Revue indépendante

- Diff examiné : [PR #17](https://github.com/betagouv/lab-anssi-rula/pull/17).
- Critères vérifiés : contrôles locaux terminés ; contrôles GitHub en cours.
- Remarques : aucune.
- Verdict : prêt à fusionner | corrections demandées
