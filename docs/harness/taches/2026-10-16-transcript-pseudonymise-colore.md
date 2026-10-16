# Tâche : retrouver et copier le transcript pseudonymisé

Statut : prêt pour relecture

## Objectif

Rendre le transcript enregistré plus lisible en colorant les pseudonymes selon leur catégorie, tout en gardant le texte pseudonymisé sélectionnable et copiable.

## Périmètre

- Inclus : rendu coloré des marqueurs persistés dans la vue du transcript, légende accessible, libellés cohérents avec la pseudonymisation et copie native du texte.
- Exclu : texte source, correspondances originales, changement de stockage, API, analyses ou parcours de relecture avant confirmation.

## Critères d’acceptation

- [x] Les six catégories de pseudonymes enregistrés ont chacune une couleur et un libellé explicite.
- [x] Les marqueurs sont rendus comme du texte interpolé, sans interpréter de HTML et sans modifier leur texte visible.
- [x] Le transcript affiché conserve les pseudonymes, le texte ordinaire, les espaces et les sauts de ligne; les identifiants `SPEAKER_XX` utilisent leurs libellés stables.
- [x] Le texte est sélectionnable et copiable avec ses marqueurs pseudonymisés; les originaux remplacés et leur correspondance ne sont pas récupérés.
- [x] Le texte ordinaire et les marqueurs inconnus restent inchangés; les locuteurs utilisent les libellés stables de la relecture.
- [x] La vue indique clairement qu’il s’agit du transcript pseudonymisé.

## Plan

1. Ajouter un découpage pur du transcript en texte ordinaire et pseudonymes reconnus, avec tests ciblés.
2. Rendre les segments en couleurs avec une légende accessible dans la vue enregistrée.
3. Vérifier la sélection et le copier-coller sur un transcript synthétique multiligne.
4. Exécuter les contrôles requis et ouvrir une PR vers `main`.

## Validation

- `cd ui && pnpm format:check`, `pnpm lint:check`, `pnpm svelte:check`, `pnpm check`, `pnpm test` (90 tests) et `pnpm build` : réussis.
- Vérification navigateur sur transcript synthétique : les six catégories, pseudonymes, libellés, accents, locuteurs et retours à la ligne sont présents. Sélection, copie et collage natifs restituent le texte pseudonymisé et ses marqueurs comme du texte; aucun mapping d’originaux n’est ajouté.
- `git diff --check` : réussi.
- `bash scripts/harness.sh complet` : backend réussi (Ruff, mypy, 325 tests réussis et 2 ignorés, couverture 99 %). Étape frontend WSL interrompue car le `node_modules` partagé Windows ne contient pas le binaire Rollup Linux `@rollup/rollup-linux-x64-gnu`; les contrôles frontend équivalents ont réussi depuis Windows.
- `bash scripts/harness.sh audit` : non exécuté, contrôle facultatif.

## Décisions

- ADR associée ou « aucune » : aucune.
- Les couleurs sont dérivées du marqueur pseudonymisé déjà enregistré; aucun original ni mapping ne sera ajouté.

## Handoff

- État du code : implémentation terminée sur `feature/transcript-pseudonymise-couleur`, créée depuis `origin/main` à jour.
- Prochaine action : pousser la branche et ouvrir une PR vers `main` pour relecture; ne pas fusionner.
- Risques ou limites : le harness complet nécessite des dépendances frontend installées pour Linux dans WSL; elles n’ont pas été ajoutées au `node_modules` partagé.

## Revue indépendante

- Diff examiné : composant de rendu, découpage des marqueurs, vue d’import et tests associés.
- Critères vérifiés : six catégories, texte exact pseudonymisé, contenu HTML échappé, locuteurs et marqueurs inconnus préservés.
- Remarques :
- Verdict : prêt pour relecture
