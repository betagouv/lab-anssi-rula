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
- [x] Le transcript brut s’affiche dans un panneau gris plafonné à 60 % de la hauteur de la fenêtre et défilable indépendamment de la page.

## Plan

1. Corriger le libellé, le lien et le verbatim transverse.
2. Séparer visuellement le sentiment et la gravité.
3. Ajouter l’onglet de consultation de l’analyse PDF à l’entretien.
4. Afficher le transcript brut dans un panneau gris défilable.

## Validation

- `bash scripts/harness.sh complet` : Ruff et mypy réussis; 286 tests backend réussis, 2 ignorés, couverture 100 %. L’étape frontend sous WSL ne trouve pas `@rollup/rollup-linux-x64-gnu` dans les dépendances Windows.
- Contrôles frontend dans un conteneur Linux avec le dépôt complet monté : `pnpm test`, `pnpm check`, `pnpm lint:check`, `pnpm format:check`, `pnpm svelte:check` et `pnpm build` réussis; 70 tests passés, Svelte sans erreur ni avertissement.
- `git diff --check` réussi.
- PR #22 : checks précédemment passés sur `fb891d3`; à relancer sur le nouveau commit après push.
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
