# Tâche : importer et analyser des transcripts PDF

Statut : implémenté, revue finale à terminer; PDF réel préparé mais pas confirmé par une personne

## Objectif

Permettre d’importer des entretiens utilisateurs et des retours BizDev en PDF, de les anonymiser, de les faire valider, puis d’analyser leur contenu individuellement et dans les corpus autorisés.

## Périmètre

- Inclus : imports PDF produit et BizDev, anonymisation et validation humaine, analyse structurée, consultation et édition, corpus projet et produit, persistance des tâches, schéma de base unifié, UI, documentation et migration.
- Exclu : OCR, envoi du PDF binaire, exécution distante de la migration, fusion et déploiement. Le texte extrait original et le contexte peuvent être transmis à Albert uniquement pendant la préparation d’anonymisation; ils restent en mémoire et ne sont ni persistés ni journalisés.

## Critères d’acceptation

- [x] PDF natif valide jusqu’à 10 Mo, 50 pages et 100 000 caractères extrait sans troncature; erreurs explicites si chiffré, illisible ou sans texte.
- [x] Tours locuteur `[7 lettres]_[2 chiffres]:` normalisés en `SPEAKER_XX`, continuité inter-pages préservée, bandeau de téléchargement supprimé et date d’origine proposée puis validée. Le préfixe `None:` devient un locuteur distinct au rôle indéterminé.
- [x] Les appels de préparation Albert reçoivent les champs originaux éphémères par groupes de fragments de tours ou de contexte de 2 000 caractères source maximum. Le modèle renvoie des plages de tokens explicites; Python résout et vérifie les tranches exactes dans le fragment fourni, puis applique les remplacements sans recherche floue ni cascade. Le garde-fou PDF et l’analyse utilisent le chemin strict exigeant un arrêt normal et un contenu non vide. PDF, texte brut, tokens et correspondances restent éphémères et ne sont ni persistés ni journalisés.
- [x] Validation humaine requise avant analyse; toutes les références et citations proviennent des tours existants et restent exactes.
- [x] Sources produit associées à produit et projet; sources BizDev associées au seul produit; analyses individuelles et transverses respectent ces périmètres.
- [x] Jobs persistants et idempotents reprenables après interruption; résultat lié à une révision, génération obsolète rejetée.
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
- Préparation Albert complète du PDF 1, contrat tokenisé, `high`, JSON Schema strict, 16 384 tokens, `temperature=1`, `top_p=1` : 18 groupes terminés, 58 remplacements et 5 locuteurs. Le texte préparé reste non confirmé et non analysé; la relecture humaine demeure obligatoire.
- E2E produit synthétique depuis un PDF natif généré en mémoire : préparation 1/1 groupe, deux identifiants synthétiques masqués, garde-fou accepté après inspection de l’aperçu, source confirmée sur un projet dédié, analyse terminée avec 2 fonctionnalités référencées, scan et trois étapes validés. E2E BizDev synthétique : projet nul, analyse terminée avec 17 extractions sur 17 contenant une référence de tour, un locuteur et un verbatim. La première confirmation BizDev a correctement exigé une date; le second envoi a utilisé la date corrigée dans la métadonnée.
- Analyse transverse du produit synthétique : 5 besoins, 2 de source `transcript_produit` et 3 de source `transcript_bizdev`; la source BizDev reste sans projet et n’apparaît pas dans le scan du projet. Les appels d’analyse répétés ont retourné les résultats existants et n’ont pas augmenté le nombre de besoins.
- Reprise du job synthétique d’analyse : le job resté en attente a été repris au démarrage du backend après correction de la factory manuelle qui recevait des objets `Depends` non résolus. L’analyse s’est terminée sans nouveau POST; les factories concrètes du worker et le journal d’erreur limité au type d’exception sont couverts.
- Migration isolée : base vide, ancienne fixture à 22 migrations, deuxième exécution sans effet et rollback préservant table témoin vérifiés sur PostgreSQL dédié.
- Harness backend isolé : `bash scripts/harness.sh complet --cible backend` réussi dans un conteneur jetable; Ruff et mypy verts, 267 tests passés, 2 intégrations PostgreSQL ignorées par défaut, couverture 100 %. Les tests du lot vérifient l’ordre source malgré les fins inversées, la limite globale partagée entre préparations, l’isolation des adaptateurs/métriques, l’annulation des groupes en file et la progression des groupes actifs.
- Frontend : ESLint, Prettier, svelte-check (0 erreur, 0 avertissement) et Vitest (60 tests) réussis dans un conteneur jetable. Navigation à cinq entrées vérifiée; le formulaire utilise `fr-upload-group`, champs DSFR, création de projet sans participant artificiel et progression basée sur les groupes validés.
- `bash scripts/harness.sh complet` : les commandes équivalentes ont passé dans des conteneurs jetables pour éviter le watcher de l’application active. Sur Windows, `uv` ne peut pas réutiliser le lien `.venv/lib64`; le conteneur jetable est le chemin de validation courant.
- `bash scripts/harness.sh audit` : non requis sauf constat de risque.
- `uv run ruff format --check src/ tests/` : 131 fichiers déjà formatés; réussite.

## Décisions

- ADR associée : [0003-transcripts-pdf.md](../../adr/0003-transcripts-pdf.md).

## Handoff

- État du code : migration unique, APIs, analyses, jobs, invalidations de révision et parcours Svelte intégrés sur `feature/transcripts-pdf` dans le worktree dédié. La checkout originale reste inchangée.
- Stack disponible sur `http://localhost:5173` avec `docker compose -p rula-pdf up --build -d`; le volume `rula-pdf_postgres_data` est distinct. Ne pas redémarrer le backend pendant les essais utilisateur; la préparation en mémoire disparaît à un redémarrage. La suppression de `--reload` dans le Dockerfile et l’expiration TTL à partir de la fin d’un job restent à appliquer lors d’un créneau sans upload actif.
- Données synthétiques persistées pour l’E2E : produit 4, projet 1, transcript produit 1, transcript BizDev 2. Ne pas supprimer sans autorisation utilisateur; préserver MQC/MSC/MSS.
- Prochaine action : revue Sol finale des derniers changements et mise à jour PR brouillon #22. Ne pas confirmer ni analyser le PDF réel sans relecture humaine de son aperçu anonymisé.
- Limites : un PDF utilisateur a perdu son jeton lors du redémarrage Uvicorn provoqué par la copie des tests sous `/app`; il faut le réimporter. Le PDF réel préparé n’est pas confirmé; les analyses E2E sont synthétiques. Le premier démarrage sur un ancien schéma efface les objets applicatifs RULA; utiliser exclusivement le worktree et son volume isolé.

## Revue indépendante

- Diff examiné : revue Sol terminée.
- Critères vérifiés : corrections backend de la revue, locuteurs, bail, verrous de révision, cinq entrées UI et contrôles finaux.
- Remarques : la préparation Albert de bout en bout sur un PDF réel reste non validée; conserver cette limite visible dans la PR.
- Verdict : PR brouillon, pas prête à merger; fusion réservée à la décision humaine.


## Lot de parallélisation

`ALBERT_PARALLELISME_ANONYMISATION` règle le plafond global du processus (défaut 8). Les préparations injectent le même exécuteur borné et fabriquent un adaptateur Albert distinct par groupe. Le résultat et les pseudonymes restent assemblés dans l’ordre source. En cas d’erreur, les tâches en attente sont annulées, les appels déjà commencés sont drainés sans réutiliser leurs réponses, et la préparation se termine en échec sans résultat partiel. La progression donne la liste triée des groupes actuellement actifs.

Vérifications du lot : backend complet (267 passés, 2 ignorés, 100 % couverture, Ruff et mypy verts), frontend complet (60 tests, ESLint, Prettier et svelte-check verts). Revues architecture et Sol : acceptées. La mesure du débit Albert réel sous huit appels simultanés reste à effectuer après intégration dans la stack locale.
