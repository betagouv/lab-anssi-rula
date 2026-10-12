# Tâche : importer et analyser des transcripts PDF

Statut : implémenté, revue finale à terminer; préparation Albert sur PDF réel non validée

## Objectif

Permettre d’importer des entretiens utilisateurs et des retours BizDev en PDF, de les anonymiser, de les faire valider, puis d’analyser leur contenu individuellement et dans les corpus autorisés.

## Périmètre

- Inclus : imports PDF produit et BizDev, anonymisation et validation humaine, analyse structurée, consultation et édition, corpus projet et produit, persistance des tâches, schéma de base unifié, UI, documentation et migration.
- Exclu : OCR, envoi du PDF binaire, exécution distante de la migration, fusion et déploiement. Le texte extrait original et le contexte peuvent être transmis à Albert uniquement pendant la préparation d’anonymisation; ils restent en mémoire et ne sont ni persistés ni journalisés.

## Critères d’acceptation

- [ ] PDF natif valide jusqu’à 10 Mo, 50 pages et 100 000 caractères extrait sans troncature; erreurs explicites si chiffré, illisible ou sans texte.
- [x] Tours locuteur `[7 lettres]_[2 chiffres]:` normalisés en `SPEAKER_XX`, continuité inter-pages préservée, bandeau de téléchargement supprimé et date d’origine proposée puis validée. Le préfixe `None:` devient un locuteur distinct au rôle indéterminé.
- [x] Les appels de préparation Albert reçoivent les champs originaux éphémères par groupes de fragments de tours ou de contexte de 2 000 caractères maximum, avec vérification locale des remplacements, regroupent les remplacements exacts, et classent les locuteurs; le garde-fou et l’analyse reçoivent uniquement les contenus anonymisés confirmés. PDF, texte brut et correspondances restent éphémères et ne sont ni persistés ni journalisés.
- [ ] Validation humaine requise avant analyse; toutes les références et citations proviennent des tours existants et restent exactes.
- [ ] Sources produit associées à produit et projet; sources BizDev associées au seul produit; analyses individuelles et transverses respectent ces périmètres.
- [ ] Jobs persistants et idempotents reprenables après interruption; résultat lié à une révision, génération obsolète rejetée.
- [x] Une migration unique initialise une base vide, remet à niveau un ancien schéma en préservant le registre/lock, et peut être rejouée sans perte des nouvelles données.
- [x] Parcours présents dans les cinq entrées produit et utilisent les composants DSFR existants.
- [x] Tests backend (100 % couverture), formatage Ruff, tests et build frontend, Harness complet et intégration PostgreSQL des écritures obsolètes vérifiés.

## Plan

1. Cartographier les services, dépôts, prompts, migrations, parcours UI et contrôles existants.
2. Implémenter parsing PDF, anonymisation structurée, schémas, validation, édition et analyses individuelles.
3. Unifier le schéma de données et ajouter jobs, dépôts, corpus projet/produit et invalidations par révision.
4. Intégrer les sources et leurs parcours aux cinq entrées UI, puis actualiser architecture, ADR et bascule de migration.
5. Valider l’extraction sur les trois PDF locaux sans les ajouter au dépôt; exécuter tests et contrôles complets, puis revue indépendante.

## Validation

- Extraction locale des trois PDF : 9/14/13 pages, 28 128/46 513/39 733 caractères de texte natif, aucune page nécessitant l’OCR; dates détectées 2026-04-07/2026-04-07/2026-08-26. Aucun texte personnel n’a été affiché.
- Smoke Albert synthétique, raisonnement `high` et JSON Schema strict : réussi en 13,9 s; remplacement exact appliqué et vérifié.
- Smoke Albert réel sur le PDF 1 : la tentative complète a reçu un 504 à 360 s. Un groupe représentatif de 1 979 caractères a été validé en 10,9 s. Pour le groupe 7 (2 000 caractères), appel non streaming : 504 après 240,1 s; l’adaptation SSE a reçu HTTP 200 en 0,342 s mais 56 272 événements sans contenu ni fin avant l’expiration globale à 428,4 s. Aucun nouvel appel n’a été lancé; le traitement réel complet reste non validé.
- Migration isolée : base vide, ancienne fixture à 22 migrations, deuxième exécution sans effet et rollback préservant table témoin vérifiés sur PostgreSQL dédié.
- Tests backend : 235 passés, 2 tests d’intégration désactivés par défaut; couverture 100 %. Les deux tests PostgreSQL activés sur le conteneur dédié passent et vérifient que les sauvegardes scan/étape attendent le verrou projet puis rejettent une révision obsolète. Frontend : 56 tests passés, Svelte sans erreur ni avertissement. Le menu du Dashboard et celui des projets présentent chacun les cinq liens requis; la page produit PDF et ses champs ont été vérifiés dans le navigateur après redémarrage de Vite (le watcher ne prenait pas en compte la modification du bind Windows avant son restart).
- `bash scripts/harness.sh complet` : réussite finale; Ruff, mypy, 235 tests backend, 100 % couverture, 56 tests frontend, contrôles Svelte, ESLint, Prettier et build UI passent.
- `bash scripts/harness.sh audit` : non requis sauf constat de risque.
- `uv run ruff format --check src/ tests/` : 131 fichiers déjà formatés; réussite.

## Décisions

- ADR associée : [0003-transcripts-pdf.md](../../adr/0003-transcripts-pdf.md).

## Handoff

- État du code : migration unique, APIs, analyses, jobs, invalidations de révision et parcours Svelte intégrés sur `feature/transcripts-pdf` dans le worktree dédié. La checkout originale reste inchangée.
- Stack de validation disponible sur `http://localhost:5173` avec `docker compose -p rula-pdf up --build -d` depuis ce worktree. Compose a créé le volume distinct `rula-pdf_postgres_data`; la migration a créé `001_schema_unifie.sql`. La vérification frontend a nécessité `docker compose -p rula-pdf restart frontend` après édition du fichier monté.
- Prochaine action : revue Sol finale, puis PR brouillon et attachement sans fusion. Le parcours de préparation réel ne doit pas être présenté comme opérationnel tant qu’Albert ne fournit pas une réponse complète et exploitable.
- Risques ou limites : la préparation segmentée a une limite opérationnelle démontrée (504 ou flux SSE vide) sur un groupe de 2 000 caractères; l’import, l’analyse et le garde-fou ne sont pas qualifiés de bout en bout sur Albert réel. Le premier démarrage sur l’ancien schéma efface les objets applicatifs RULA; l’utilisateur doit démarrer uniquement le worktree de cette branche avec son volume isolé.

## Revue indépendante

- Diff examiné : revue Sol terminée.
- Critères vérifiés : corrections backend de la revue, locuteurs, bail, verrous de révision, cinq entrées UI et contrôles finaux.
- Remarques : la préparation Albert de bout en bout sur un PDF réel reste non validée; conserver cette limite visible dans la PR.
- Verdict : PR brouillon, pas prête à merger; fusion réservée à la décision humaine.
