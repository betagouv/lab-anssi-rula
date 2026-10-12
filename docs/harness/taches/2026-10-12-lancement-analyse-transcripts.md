# Tâche : clarifier le lancement et l’affichage de l’analyse des transcripts

Statut : prête à revoir

## Objectif

Rendre le résultat d’analyse prévisible et visible pendant et après son calcul pour les transcripts PDF produit et BizDev.

## Périmètre

- Inclus : onglets d’analyse et de transcript, consignes avant lancement, états de chargement, réussite, erreur et relance dans l’écran du transcript enregistré.
- Exclu : API, persistance, format et calcul de l’analyse.

## Critères d'acceptation

- [x] L’écran du transcript propose les onglets « Analyse générée » et « Transcript brut », avec l’analyse sélectionnée par défaut.
- [x] Avant lancement, l’utilisateur voit que l’analyse apparaîtra dans son onglet et peut la lancer sans défiler le verbatim.
- [x] Pendant le traitement, un libellé, un indicateur animé et un statut accessible indiquent le chargement sans faux pourcentage.
- [x] Le résultat apparaît dans l’onglet d’analyse sans défilement supplémentaire.
- [x] Si l’utilisateur consulte le transcript à la fin du traitement, une notification persistante et une action « Voir l’analyse » lui indiquent où trouver le résultat.
- [x] En cas d’échec, l’erreur est visible et l’utilisateur peut relancer le traitement.
- [x] Les onglets fonctionnent au clavier et restent utilisables sur mobile.

## Plan

1. Ajouter la navigation accessible entre les deux vues dans l’écran du transcript enregistré.
2. Rendre explicites les états initial, en cours, terminé et en échec, avec un accès direct à une analyse terminée.
3. Ajouter les tests ciblés, contrôler le rendu responsive et exécuter les contrôles du dépôt.
4. Créer un commit atomique et ouvrir une PR empilée sur la branche de consultation des transcripts.

## Validation

- `pnpm test` : 12 fichiers, 79 tests réussis ; Svelte check sans erreur ni avertissement.
- `pnpm lint:check`, `pnpm format:check` et `pnpm build` : réussis.
- `pnpm svelte:check` : 0 erreur, 0 avertissement.
- `bash scripts/harness.sh complet --cible backend` : Ruff et mypy réussis ; 286 tests réussis, 2 ignorés ; couverture 100 %.
- `bash scripts/harness.sh complet` : backend réussi, phase frontend indisponible dans WSL car le `node_modules` Windows ne fournit pas le binaire Rollup Linux `@rollup/rollup-linux-x64-gnu`. Les contrôles frontend ont tous réussi directement sous Windows.
- Vérification manuelle : onglets et panneau gris sur bureau et largeur mobile ; navigation clavier par flèches ; statut de chargement vérifié dans le DOM accessible.
- `git diff --check` : réussi.
- `gh pr checks 23 --watch` : GitGuardian Security Checks réussi après le push.

## Décisions

- ADR associée : aucune.
- La PR #23 dépend de la PR #26 (`feature/transcripts-pdf-product-ui`), elle-même empilée sur les PR #22, #24 et #25.

## Handoff

- État du code : implémentation validée dans un worktree dédié, branche `feature/ux-analyse-transcripts`.
- Prochaine action : suivre les checks de la PR #23, puis intégrer la chaîne dans l’ordre #22, #24, #25, #26 et #23.
- Risques ou limites : les branches sont empilées ; respecter l’ordre de fusion ou réviser les bases après chaque fusion.

## Revue indépendante

- Diff examiné : par l’implémenteur avant commit ; PR [#23](https://github.com/betagouv/lab-anssi-rula/pull/23) ouverte en brouillon.
- Critères vérifiés : contrôles frontend, backend, rendu responsive, navigation clavier et annonces de statut.
- Remarques : le harness complet ne peut pas lancer son étape frontend depuis WSL avec les dépendances Windows ; les mêmes contrôles frontend passent sous Windows.
- Verdict : prêt à revoir.
