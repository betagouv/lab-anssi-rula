# ADR 0001 : harness local et agnostique des agents

Date : 2026-08-24

## Contexte

RULA doit pouvoir être développé avec plusieurs agents de code tout en gardant des contrôles reproductibles, une reprise de contexte claire et une revue humaine. Le projet est de taille réduite et ne nécessite pas de plateforme d'orchestration.

## Décision

Le dépôt adopte un harness local fondé sur un guide commun, des fiches de tâche, des ADR et un lanceur Python. Qlty est limité à un audit local non bloquant ; aucun résultat ni code n'est envoyé vers Qlty Cloud.

## Conséquences

- Bénéfice : méthode commune, traces versionnées et contrôles utilisables sous Windows.
- Coût ou limite : la coordination reste manuelle et la dette Qlty est priorisée dans des tâches séparées.
- Alternatives écartées : orchestrateur d'agents et intégration Qlty Cloud.
