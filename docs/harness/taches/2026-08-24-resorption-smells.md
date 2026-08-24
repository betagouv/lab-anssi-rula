# Tâche : résorption des smells Qlty

Statut : prête à revoir

## Objectif

Supprimer les 15 constats Qlty détectés sur la branche du harness local, sans modifier le comportement fonctionnel de RULA.

## Périmètre

- Inclus : paramètres de services, duplications des dépôts, client HTTP partagé et parseur de routes.
- Exclu : évolution fonctionnelle et changement de seuils Qlty.

## Critères d'acceptation

- [x] Qlty ne remonte plus de smell sur l'ensemble du dépôt.
- [x] Les contrôles backend et frontend restent verts.
- [x] La couverture Python reste à 100 %.

## Validation

- `qlty smells --all` : 0 constat.
- `uv run python scripts/harness.py complet` : validé, 73 tests Python à 100 % de couverture et 30 tests frontend.
- `uv run python scripts/harness.py audit` : validé, SARIF Qlty sans smell ni alerte Bandit.

## Handoff

- État du code : les abstractions partagées conservent les interfaces métier et les routes existantes.
- Prochaine action : revue du diff puis fusion de la PR.
- Risques ou limites : les métriques Qlty restent un indicateur de suivi, pas un score de qualité global.

## Revue indépendante

- Diff examiné : à faire.
- Critères vérifiés : à faire.
- Remarques : à faire.
- Verdict : à faire.
