# Tâche : corriger la consultation des transcripts produit

Statut : prête à revoir

## Objectif

Rendre la source produit, son verbatim et son analyse PDF faciles à consulter depuis l’analyse transverse et la page d’entretien.

## Périmètre

- Inclus : libellé et lien des transcripts produit dans l’analyse transverse, onglets analyse/transcript brut, affichage séparé de la gravité.
- Exclu : calcul des analyses, données persistées et API métier.

## Critères d’acceptation

- [x] Un transcript PDF produit est libellé comme transcript produit, ouvre son entretien, et son verbatim reste visible dans l’analyse transverse.
- [x] La page d’entretien permet d’alterner entre l’analyse PDF générée et le transcript brut.
- [x] La gravité apparaît sur une ligne distincte du sentiment.

## Plan

1. Corriger le libellé, le lien et le verbatim transverse.
2. Séparer visuellement le sentiment et la gravité.
3. Ajouter l’onglet de consultation de l’analyse PDF à l’entretien.

## Validation

- Commandes ciblées : `pnpm test`, `pnpm check`, `pnpm lint:check`, `pnpm format:check` et `pnpm build` en conteneur Linux jetable; 70 tests réussis, Svelte sans erreur ni avertissement.
- `bash scripts/harness.sh complet` : Ruff et mypy réussis; 286 tests backend réussis, 2 ignorés, couverture 100 %. L’étape front lancée via WSL ne trouve pas le binaire Rollup Linux dans les dépendances Windows; les commandes frontend équivalentes ont réussi en conteneur Linux jetable.
- PR #22 : tous les checks GitHub réussissent, tête `fb891d3`.
- `bash scripts/harness.sh audit` : non requis.

## Décisions

- ADR associée : aucune.

## Handoff

- État du code : les trois critères sont corrigés et validés sur la PR #22, ouverte en brouillon.
- Prochaine action : revue indépendante; la fusion reste à décider par un humain.
- Risques ou limites : aucun identifié.

## Revue indépendante

- Diff examiné : relecture locale de l’implémentation; revue indépendante en attente.
- Critères vérifiés : libellé, lien, verbatim, onglets et gravité.
- Remarques : aucune identifiée pendant la relecture locale.
- Verdict : en attente d’une revue indépendante.
