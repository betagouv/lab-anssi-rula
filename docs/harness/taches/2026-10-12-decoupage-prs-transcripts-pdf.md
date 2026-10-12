# Tâche : découper la pile de transcripts PDF en PR empilées

Statut : prête à revoir

## Objectif

Répartir l’ancienne PR #22 en changements cohérents, plus courts à relire, et conserver le sommet de la pile comme checkout local.

## Périmètre

- Inclus : découpage des dépôts PDF, de l’analyse, des routes API, de l’import, des vues produit et de l’UX du lancement en étapes empilées.
- Exclu : fusion des PR et modification des fichiers locaux de configuration Compose.

## Critères d’acceptation

- [x] La branche `feature/transcripts-pdf` ne contient que l’unification de la persistance et son test de révision.
- [x] `feature/transcripts-pdf-depots` contient le contrat et les dépôts PDF avec leurs tests.
- [x] Les branches `feature/transcripts-pdf-core`, `feature/transcripts-pdf-api`, `feature/transcripts-pdf-import`, `feature/transcripts-pdf-product-ui` et `feature/ux-analyse-transcripts` suivent dans cet ordre.
- [x] Le checkout principal reste sur `feature/ux-analyse-transcripts` et les fichiers locaux non suivis sont préservés.
- [x] Les PR restent ouvertes en brouillon ; aucune n’est fusionnée.

## Plan

1. Retirer les dépôts PDF de la PR de persistance et couvrir la réussite du contrôle de révision.
2. Créer une étape dédiée aux dépôts PDF, puis reconstruire les étapes suivantes sur leurs nouvelles bases.
3. Valider les contrôles backend, frontend et les checks GitHub.

## Validation

- PR de persistance : `bash scripts/harness.sh complet --cible backend` réussi ; 158 tests réussis, 2 ignorés, couverture 100 %.
- Étape des dépôts : `bash scripts/harness.sh complet --cible backend` réussi ; 165 tests réussis, 2 ignorés, couverture 100 %.
- Sommet de pile : Ruff, mypy et backend réussis ; 294 tests réussis, 2 ignorés, couverture 100 %.
- Frontend Windows : lint, format, Svelte check, 79 tests et build réussis.
- Le harness complet lancé depuis le nouveau worktree s’arrête à l’étape frontend car ce worktree ne contient pas `node_modules`; les mêmes contrôles frontend ont été exécutés avec succès depuis le checkout principal.
- `git diff --check` réussi.
- Checks GitHub : à vérifier après publication des branches réempilées.

## Décisions

- ADR associée : aucune.

## Handoff

- État du code : pile reconstruite localement, sans fusion ; PRs brouillonnes à republier et à vérifier.
- Prochaine action : vérifier les checks GitHub de chaque étape.
- Risques ou limites : les branches restent dépendantes de l’ordre de fusion documenté ci-dessus.

## Revue indépendante

- Diff examiné : la séparation des étapes et le test de couverture des dépôts mémoire.
- Critères vérifiés : contrôles backend et frontend locaux, checkout principal et fichiers locaux préservés.
- Remarques : revue indépendante en attente.
- Verdict : prêt à revoir.