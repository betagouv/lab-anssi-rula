# Tâche : supprimer les projets et transcripts avec confirmation

Statut : prêt pour PR

## Objectif

Permettre la suppression définitive d’un projet ou d’un transcript, avec une confirmation explicite et la suppression de toutes les données dépendantes.

## Périmètre

- Inclus : suppression des projets, entretiens UX et transcripts PDF produit/BizDev; modales DSFR exigeant la saisie exacte de `JE CONFIRME`; suppression des analyses et données dérivées liées.
- Exclu : suppression des données produit sans lien avec le projet supprimé; restauration ou suppression logique.

## Critères d’acceptation

- [x] Un projet peut être supprimé depuis sa page; la route API répond 204 ou 404 et PostgreSQL supprime ses données dépendantes.
- [x] Les trois types de transcript peuvent être supprimés depuis leur liste; leurs analyses et données dérivées disparaissent en cascade.
- [x] Les boutons ouvrent une modale DSFR décrivant les conséquences; la suppression reste impossible tant que `JE CONFIRME` n’est pas saisi exactement.
- [x] Annuler ne modifie aucune donnée; une erreur de l’API est annoncée et permet de réessayer; une réussite met à jour la navigation ou la liste.
- [x] La modale utilise le comportement clavier et la grille responsive DSFR.

## Plan

1. Ajouter la route API de suppression de projet en réutilisant le dépôt existant.
2. Ajouter le client de suppression des transcripts PDF et les actions de suppression des trois types dans les vues concernées.
3. Ajouter la confirmation DSFR avec champ de saisie, état désactivé et retour d’erreur/succès.
4. Vérifier les cascades existantes et ajouter seulement les validations utiles au scénario de suppression.
5. Exécuter les contrôles backend et frontend requis, puis ouvrir une PR distincte.

## Validation

- `uv run pytest tests/api/test_projets.py tests/api/test_transcripts_pdf.py` : 33 tests passés.
- `pnpm test` (Windows) : 80 tests passés, Svelte sans erreur.
- `pnpm lint:check`, `pnpm format:check` et `pnpm svelte:check` (Windows) : succès.
- `bash scripts/harness.sh complet` : succès; 295 tests backend passés, 2 tests d’intégration ignorés; 80 tests frontend passés; `pnpm check`, lint, format et build réussis.
- La cascade PostgreSQL a été vérifiée dans `migrations/001_schema_unifie.sql`; les deux tests qui requièrent une base de données sont ignorés par la configuration locale.
- `bash scripts/harness.sh audit` : non requis.

## Décisions

- La migration actuelle possède déjà les clés étrangères et déclencheurs de cascade nécessaires; aucune migration n’est prévue si les validations le confirment.
- Le déploiement DEMO ne s’exécute que depuis `main`; la fusion de la PR reste une décision humaine.

## Handoff

- État du code : implémentation validée dans un worktree dédié depuis `main`.
- Prochaine action : créer un commit atomique, pousser la branche et ouvrir la PR dédiée; après intégration dans `main`, lancer le déploiement DEMO.
- Risques ou limites : suppression définitive des données rattachées après confirmation.

## Revue indépendante

- Diff examiné : route de suppression, cascade SQL existante, adaptateur mémoire, modale DSFR et trois interfaces.
- Critères vérifiés : code et tests locaux.
- Remarques : aucune migration ajoutée; pas de test d’intégration PostgreSQL actif dans cet environnement.
- Verdict : prêt pour PR.
