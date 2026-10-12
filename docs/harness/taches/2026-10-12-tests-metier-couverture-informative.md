# Tâche : privilégier les tests métier à un seuil global de couverture

Statut : terminée

## Objectif

Faire porter les tests sur les règles métier utiles et garder la couverture comme indicateur, sans exiger 100 % de lignes couvertes.

## Périmètre

- Inclus : retirer le seuil global de couverture et préciser la règle dans `AGENTS.md`.
- Exclu : ajouter des tests uniquement pour couvrir des branches sans valeur métier.

## Critères d'acceptation

- [x] `pytest` produit toujours le rapport de couverture, sans échec lié à un seuil de lignes.
- [x] Les consignes privilégient les tests des règles métier utiles.

## Validation

- `uv run ruff check src/ tests/` : réussi.
- `uv run mypy` : réussi, 129 fichiers source.
- `uv run pytest` : réussi, 222 tests passés, 2 ignorés ; une branche non exercée, couverture indicative à 99,95 %.
- `git diff --check` : réussi.

## Décisions

- ADR associée : aucune.

## Handoff

- État du code : règle de couverture ajustée pour privilégier la valeur métier des tests.
- Prochaine action : vérifier les contrôles puis pousser le commit dans la PR #24.
- Risques ou limites : la couverture reste informative et n'est plus bloquante.

## Revue indépendante

- Diff examiné : configuration pytest et consignes de tests.
- Critères vérifiés : la couverture reste affichée sans seuil bloquant ; aucun test ajouté uniquement pour atteindre un pourcentage.
- Remarques : aucune.
- Verdict : prêt à fusionner après les checks GitHub.
