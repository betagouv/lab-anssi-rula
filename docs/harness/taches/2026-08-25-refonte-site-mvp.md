# Tâche : Refonte MVP RULA par produit

Statut : terminée

## Objectif

Reconstruire le MVP autour des produits MQC, MSC et MSS, de leurs projets de recherche et des analyses validées.

## Périmètre

- Inclus : reset métier, modèle produit/projet/entretien, validation, scan, dashboard, routage et interface Figma.
- Exclu : comptes, fichiers PDF/DOCX, administration du catalogue, intégration visuelle BizDev et FeatureBase.

## Critères d'acceptation

- [x] Une carte produit ouvre ses projets et son dashboard.
- [x] Un entretien ne peut être enregistré sans confirmation ni validation.
- [x] Une source peut rejoindre un projet existant ; les homonymes sont refusés dans un produit.
- [x] Un scan est généré, modifiable et validable avant son détail.
- [x] Les imports CSV BizDev et FeatureBase sont filtrés par produit.
- [x] Les écrans Figma sont vérifiés en navigateur à 1440 px.

## Plan

1. Réinitialiser les données et poser le modèle produit/projet.
2. Exposer les parcours et validations backend.
3. Refaire l'interface et le routage.
4. Rattacher les imports CSV aux produits.
5. Vérifier les contrôles complets et le rendu.

## Validation

- Commandes ciblées pendant l'itération : `bash scripts/harness.sh rapide --cible backend`
- `uv run ruff check src/ tests/ && uv run mypy && uv run pytest` : 107 tests, couverture 100 %.
- `pnpm svelte:check && pnpm lint:check && pnpm format:check && pnpm test` : 40 tests, sans erreur ni avertissement.
- `bash scripts/harness.sh complet` : backend validé ; l’étape frontend échoue uniquement depuis WSL car ses dépendances natives Windows cherchent le binaire Rollup Linux.

## Décisions

- ADR associée ou « aucune » : aucune
- Le reset ne conserve que le catalogue MQC, MSC et MSS.
- Les briefs et transcripts UX sont saisis en texte ; les CSV restent réservés à BizDev et FeatureBase.

## Handoff

- État du code : migrations 015 et 016 exécutées sur `rula-postgres-1`, catalogue MQC/MSC/MSS seul conservé, projets réinitialisés.
- Prochaine action : créer la PR depuis `refonte-site-mvp`.
- Risques ou limites : Figma MCP a atteint le quota du siège View ; la fidélité s’appuie sur les maquettes PNG locales.

## Revue indépendante

- Diff examiné : parcours, schéma et routes relus localement.
- Critères vérifiés : contrôles backend, contrôles frontend natifs et parcours vide à 1440 px.
- Remarques : le dashboard reprend les projets du produit et reste vide sans données ; les maquettes complémentaires BizDev/FeatureBase restent hors de la navigation MVP.
- Verdict : prêt pour revue humaine.

## Refactor de la PR

- Les composants d’entretien, progression, garde-fou et imports produit sont mutualisés.
- Les fixtures du parcours projet et les mappings SQL sont factorisés.
- L’historique est regroupé par modèle, API, shell, vues, imports et documentation.
- Les contrôles backend et frontend restent verts avec la couverture backend à 100 %.
