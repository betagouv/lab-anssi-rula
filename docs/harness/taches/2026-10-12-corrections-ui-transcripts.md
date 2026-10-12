# Tâche : corriger la consultation des transcripts produit

Statut : en cours

## Objectif

Rendre la source produit, son verbatim et son analyse PDF faciles à consulter depuis l’analyse transverse et la page d’entretien.

## Périmètre

- Inclus : libellé et lien des transcripts produit dans l’analyse transverse, onglets analyse/transcript brut, affichage séparé de la gravité.
- Exclu : calcul des analyses, données persistées et API métier.

## Critères d’acceptation

- [x] Un transcript PDF produit est libellé comme transcript produit, ouvre son entretien, et son verbatim reste visible dans l’analyse transverse.
- [x] La page d’entretien permet d’alterner entre l’analyse PDF générée et le transcript brut.
- [ ] La gravité apparaît sur une ligne distincte du sentiment.

## Plan

1. Corriger le libellé, le lien et le verbatim transverse.
2. Séparer visuellement le sentiment et la gravité.
3. Ajouter l’onglet de consultation de l’analyse PDF à l’entretien.

## Validation

- Commandes ciblées pendant l’itération : `pnpm lint:check`, `pnpm format:check`, `pnpm svelte:check`, `pnpm test` dans `ui/` ; 69 tests réussis, Svelte sans erreur ni avertissement.
- `bash scripts/harness.sh complet` : à compléter.
- `bash scripts/harness.sh audit` : non requis.

## Décisions

- ADR associée : aucune.

## Handoff

- État du code : deux premiers critères corrigés et validés; le retour à la ligne de la gravité reste à faire.
- Prochaine action : implémenter les trois critères en commits atomiques.
- Risques ou limites : aucun identifié.

## Revue indépendante

- Diff examiné : en attente.
- Critères vérifiés : en attente.
- Remarques : en attente.
- Verdict : corrections demandées.
