# Tâche : harness qualité local

Statut : prête à revoir

## Objectif

Fournir un cadre local, léger et commun aux agents pour développer RULA avec des contrôles qualité reproductibles.

## Périmètre

- Inclus : guide commun, modèles versionnés, lanceur local, audit Qlty non bloquant et checklist de PR.
- Exclu : orchestrateur d'agents, Qlty Cloud, publication SARIF, corrections de dette existante et évolution de la CI.

## Critères d'acceptation

- [x] Les trois rôles et le recours aux worktrees sont documentés.
- [x] Les profils `rapide`, `complet` et `audit` existent.
- [x] L'audit produit des SARIF locaux sans appliquer de correctif.
- [x] Bandit ignore les tests et ESLint/Ruff ne sont pas lancés par Qlty.

## Plan

1. Ajouter le guide et les modèles de travail.
2. Configurer Qlty pour l'audit local minimal.
3. Ajouter et valider le lanceur local.

## Validation

- Commandes ciblées pendant l'itération : profils rapides backend et frontend validés.
- `bash scripts/harness.sh complet` : validé, 73 tests Python à 100 % de couverture et 30 tests frontend.
- `bash scripts/harness.sh audit` : validé, 15 smells historiques et aucune alerte Bandit.

## Décisions

- ADR associée : [0001-harness-local](../../adr/0001-harness-local.md).

## Handoff

- État du code : harness initial validé localement.
- Prochaine action : faire relire le diff puis ouvrir la pull request.
- Risques ou limites : Qlty reste un audit local non bloquant.

## Revue indépendante

- Diff examiné : à faire.
- Critères vérifiés : à faire.
- Remarques : à faire.
- Verdict : à faire.
