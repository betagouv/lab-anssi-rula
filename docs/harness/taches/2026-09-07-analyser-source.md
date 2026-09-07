# Tâche : Alignement de l’action d’analyse des sources

Statut : prête à revoir

## Objectif

Présenter la même action d’analyse et d’insertion des sources depuis le
Dashboard et la liste des projets produit.

## Périmètre

- Inclus : composant d’action partagé et intégration dans les deux vues produit.
- Exclu : backend, API, schéma de données et action de la vue détail d’un projet.

## Critères d’acceptation

- [x] Le Dashboard affiche « Analyser une source de données ».
- [x] La liste des projets affiche le même bouton avec le même libellé.
- [x] Le bouton ouvre les choix transcript, BizDev et FeatureBase.
- [x] Les parcours d’insertion et d’analyse existants restent inchangés.

## Plan

1. Mutualiser le bouton et son menu de sources.
2. Remplacer les actions du Dashboard et de la liste des projets.
3. Contrôler le frontend et ouvrir la PR empilée sur la PR #18.

## Validation

- Commandes ciblées pendant l’itération : contrôles directs des binaires frontend
  installés : svelte-check, ESLint, Prettier, Vitest (53 tests), TypeScript et
  build Vite, tous validés.
- `bash scripts/harness.sh complet` : backend validé ; étape frontend bloquée par
  la résolution de `pnpm.cmd` Windows depuis Bash. Les contrôles frontend
  équivalents ont été validés directement.
- `bash scripts/harness.sh audit` : non requis pour cette modification.

## Décisions

- ADR associée : aucune.

## Handoff

- État du code : implémentation terminée sur `feature/analyser-source`.
- Prochaine action : faire relire la PR #19.
- Risques ou limites : aucun changement backend prévu.

## Revue indépendante

- Diff examiné : [PR #19](https://github.com/betagouv/lab-anssi-rula/pull/19),
  composant partagé et intégration dans les deux vues produit.
- Critères vérifiés : contrôles frontend et backend validés.
- Remarques :
- Verdict : prêt à fusionner | corrections demandées
