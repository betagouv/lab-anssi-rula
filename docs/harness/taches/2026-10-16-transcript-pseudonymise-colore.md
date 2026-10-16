# Tâche : retrouver et copier le transcript pseudonymisé

Statut : prêt pour relecture

## Objectif

Rendre le transcript enregistré et son mode de modification plus lisibles en colorant les pseudonymes selon leur catégorie, tout en gardant le texte pseudonymisé sélectionnable et copiable. Demander une confirmation explicite avant le premier enregistrement définitif.

## Périmètre

- Inclus : rendu coloré des marqueurs persistés dans la vue et les champs de modification du transcript et du contexte, légende accessible, copie native du texte, confirmation avant le premier enregistrement définitif.
- Exclu : texte source, correspondances originales, changement de stockage, API ou analyses.

## Critères d’acceptation

- [x] Les six catégories de pseudonymes enregistrés ont chacune une couleur et un libellé explicite.
- [x] Les marqueurs sont rendus comme du texte interpolé, sans interpréter de HTML et sans modifier leur texte visible.
- [x] Le transcript affiché conserve les pseudonymes, le texte ordinaire, les espaces et les sauts de ligne; les identifiants `SPEAKER_XX` utilisent leurs libellés stables.
- [x] Le texte est sélectionnable et copiable avec ses marqueurs pseudonymisés; les originaux remplacés et leur correspondance ne sont pas récupérés.
- [x] Le texte ordinaire et les marqueurs inconnus restent inchangés; les locuteurs utilisent les libellés stables de la relecture.
- [x] La vue indique clairement qu’il s’agit du transcript pseudonymisé.
- [x] Les champs transcript et contexte gardent des zones de texte éditables et affichent les marqueurs avec leur couleur de catégorie, sans décaler le texte.
- [x] Le premier enregistrement affiche une modale DSFR accessible qui explique la perte définitive des valeurs masquées et permet de revenir à la relecture.
- [x] La mise à jour d’un transcript déjà enregistré ne promet pas de récupérer les valeurs d’origine supprimées.

## Plan

1. Ajouter un découpage pur du transcript en texte ordinaire et pseudonymes reconnus, avec tests ciblés.
2. Rendre les segments en couleurs avec une légende accessible dans la vue enregistrée et les champs éditables.
3. Ajouter la confirmation DSFR avant la première sauvegarde définitive.
4. Vérifier l’édition, les couleurs et les actions de la modale sur des données synthétiques.
5. Exécuter les contrôles requis et mettre à jour la PR #35.

## Validation

- `cd ui && pnpm format:check`, `pnpm lint:check`, `pnpm svelte:check`, `pnpm check`, `pnpm test` (101 tests après ces changements) et `pnpm build` : réussis.
- Vérification navigateur sur transcript synthétique : les six catégories, pseudonymes, libellés, accents, locuteurs et retours à la ligne sont présents. Sélection, copie et collage natifs restituent le texte pseudonymisé et ses marqueurs comme du texte; aucun mapping d’originaux n’est ajouté.
- `git diff --check` : réussi.
- `bash scripts/harness.sh complet` : backend réussi (Ruff, mypy, 334 tests réussis et 2 ignorés, couverture 99 %). Étape frontend WSL interrompue car le `node_modules` partagé Windows ne contient pas le binaire Rollup Linux `@rollup/rollup-linux-x64-gnu`; aucune dépendance n’a été installée dans cet environnement partagé.
- L’agrégat CodeQL de la #34 a signalé un niveau élevé (`py/clear-text-storage-sensitive-data`) sur le jeton aléatoire placé dans le cookie `HttpOnly`; l’empreinte seule est conservée en RAM côté serveur. Ce signalement reste à suivre.
- `bash scripts/harness.sh audit` : non exécuté, contrôle facultatif.
- Contrôles GitHub de la nouvelle tête de la #35 : Backend Python, Frontend Svelte, CodeQL, analyses de langages et GitGuardian réussis.
- Tests ciblés des deux composants : 4 tests réussis. Vérification navigateur synthétique avec DSFR : six catégories colorées, édition directe d’un pseudonyme, ouverture de la modale par clic et clavier, fermeture par bouton et Échap.
- Contrôles frontend Windows après les derniers changements : `pnpm format:check`, `pnpm lint:check`, `pnpm check`, `pnpm test` (101 réussis) et `pnpm build` réussis.

## Décisions

- ADR associée ou « aucune » : aucune.
- Les couleurs sont dérivées du marqueur pseudonymisé déjà enregistré; aucun original ni mapping ne sera ajouté.

## Handoff

- Base : PR #34 fusionnée dans `main` au commit `17a56e2`.
- État du code : branche #35 rebasée sur `origin/main`; le rendu coloré reçoit aussi les libellés stables des locuteurs et garde les transformations de la #34. Le mode Modifier colore transcript et contexte sans remplacer leurs champs éditables; la première sauvegarde demande une confirmation irréversible.
- PR : [#35](https://github.com/betagouv/lab-anssi-rula/pull/35), ouverte vers `main` pour relecture; la #35 reste non fusionnée.
- Contrôles GitHub de la nouvelle tête : tous réussis après le push avec lease.
- Risques ou limites : le harness complet nécessite des dépendances frontend installées pour Linux dans WSL; elles n’ont pas été ajoutées au `node_modules` partagé.

## Revue indépendante

- Diff examiné : composant de rendu, découpage des marqueurs, vue d’import et tests associés.
- Critères vérifiés : six catégories, texte pseudonymisé exact, contenu HTML échappé, libellés de locuteurs et marqueurs inconnus préservés.
- Remarques :
- Verdict : prêt pour relecture
