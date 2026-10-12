# Tâche : découper la pile de transcripts PDF en PR empilées

Statut : prête à revoir

## Objectif

Répartir l’ancienne PR #22 en changements cohérents, plus courts à relire, et conserver le sommet de la pile comme checkout local.

## Périmètre

- Inclus : dépôts PDF, analyse, routes API, import, consultation produit et UX de lancement.
- Exclu : fusion des PR et modification des fichiers locaux de configuration Compose.

## Critères d’acceptation

- [x] La PR #22 porte l’unification de la persistance et son test de révision.
- [x] La PR #27 isole le contrat et les dépôts PDF avec leurs tests.
- [x] La chaîne continue avec les PR #24, #28, #25, #26 et #23, chacune basée sur la précédente.
- [x] Le checkout principal est sur `feature/ux-analyse-transcripts`; les fichiers locaux non suivis sont préservés.
- [x] Les PR restent ouvertes en brouillon ; aucune n’est fusionnée.

## Plan

1. Réduire le périmètre de la PR de persistance et couvrir la réussite du contrôle de révision.
2. Isoler les dépôts PDF dans une PR dédiée.
3. Empiler l’analyse, les API, l’import et les interfaces dans des PR distinctes.
4. Valider le code localement et vérifier les checks GitHub.

## Validation

- PR #22 : `bash scripts/harness.sh complet --cible backend` réussi ; 158 tests réussis, 2 ignorés, couverture 100 %.
- PR #27 : `bash scripts/harness.sh complet --cible backend` réussi ; 165 tests réussis, 2 ignorés, couverture 100 %.
- Sommet : Ruff, mypy et backend réussis ; 294 tests réussis, 2 ignorés, couverture 100 %.
- Frontend Windows : lint, format, Svelte check, 79 tests et build réussis.
- Dans le nouveau worktree, le harness complet passe le backend mais ne trouve pas `node_modules` pour le frontend ; les mêmes contrôles frontend ont réussi depuis le checkout principal.
- `git diff --check` réussi.
- GitHub : tous les checks de la PR #22 passent ; GitGuardian passe sur les PR #23, #24, #25, #26, #27 et #28.

## Décisions

- ADR associée : aucune.

## Handoff

- État du code : les sept PR sont ouvertes en brouillon, empilées dans l’ordre #22 → #27 → #24 → #28 → #25 → #26 → #23.
- Prochaine action : revue humaine de la pile, puis fusion dans cet ordre.
- Risques ou limites : les branches restent dépendantes de l’ordre de fusion indiqué.

## Revue indépendante

- Diff examiné : le découpage des changements et les tests ajoutés pour les dépôts mémoire.
- Critères vérifiés : validations backend/frontend locales, état des PR, checkout principal et fichiers locaux préservés.
- Remarques : revue indépendante en attente.
- Verdict : prêt à revoir.