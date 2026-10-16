# Tâche : relecture interactive de la pseudonymisation

Statut : correction de chevauchement en attente de revue

## Objectif

Permettre de relire les occurrences pseudonymisées après préparation d’un transcript et de modifier les masques avant confirmation, avec la source originale disponible uniquement pendant cette préparation temporaire.

## Périmètre

- Inclus : modèle d’occurrences source, préparation temporaire, état de relecture accessible au clavier et au tactile, édition des catégories, ajout de masques par sélection, annulation/rétablissement, rôles de locuteurs et prompt partagé Produit/BizDev.
- Exclu : stockage des originaux, modification des contrats POST/PUT de confirmation, redesign du shell DSFR, changement des analyses historiques.

## Critères d'acceptation

- [x] Les textes source originaux et les plages exactes des occurrences sont fournis dans la seule réponse temporaire de préparation, sans journalisation ni persistance.
- [x] La relecture affiche le document sur environ 75 % de la largeur et le détail du masque sélectionné sur 25 %; le survol révèle temporairement l’original en place sans changement de mise en page, le clic bascule globalement le masque exact.
- [x] Les masques actifs et inactifs restent visibles et cliquables; une occurrence regroupe toutes les mentions identiques exactes dans le transcript et le contexte.
- [x] Le détail du masque sélectionné expose son original en lecture seule, sa catégorie modifiable, son compteur, sa révélation et sa bascule; les catégories et pseudonymes restent cohérents après modification.
- [x] Une sélection de texte propose une catégorie puis attend une action explicite pour créer un masque global exact; un chevauchement partiel incompatible est refusé atomiquement.
- [x] Annuler et rétablir couvrent ajouts, activations et catégories sans perdre les modifications suivantes.
- [x] Navigation clavier, focus, Échap et commandes tactiles permettent de révéler et parcourir sans dépendre du survol.
- [x] Le POST/PUT de confirmation transmet uniquement le texte projeté et les locuteurs; validation existante, correction des rôles et confirmation sont préservées.
- [x] Les noms de rôles rendus sont `Interne · N`, `Externe · N` et `Indéterminé · N`; les identifiants techniques `SPEAKER_XX` sont conservés.
- [x] La même relecture est utilisée pour Produit et BizDev, avec le prompt partagé mis à jour pour la classification prudente des technologies/produits et la préservation des fonctions professionnelles.
- [x] Les tests métier et la preuve de parcours navigateur couvrent les occurrences globales, collisions, Unicode Python/JavaScript, historique, interactions desktop/mobile et textes longs.

## Plan

1. Étendre le modèle temporaire de préparation avec les sources originales et les occurrences validées.
2. Construire un modèle frontend pur pour les plages, la projection, les pseudonymes stables et l’historique.
3. Intégrer un écran de relecture à la préparation existante et préserver le flux de confirmation.
4. Ajouter les tests DeTest et un scénario navigateur synthétique sans persistance.
5. Exécuter les contrôles requis, demander la revue Sol, puis préparer une PR brouillon sans fusion.

## Validation

- `bash scripts/harness.sh complet` : Ruff, mypy et pytest passent (329 tests, deux ignorés); le sous-contrôle frontend WSL échoue car `@rollup/rollup-linux-x64-gnu` manque dans les dépendances Windows partagées.
- Contrôles frontend Windows : lint, format, `svelte-check` (zéro erreur/avertissement), Vitest (90 tests), TypeScript et build passent.
- Après le correctif : `uv run ruff check .`, format des quatre fichiers concernés, `uv run mypy` (135 fichiers) et `uv run pytest -q --no-cov` passent (332 réussis, deux ignorés, un avertissement Starlette préexistant). Côté Windows, lint, format, `svelte-check` (zéro erreur/avertissement), Vitest (90 tests), TypeScript et build passent.
- `uv run ruff format --check` passe sur les fichiers backend modifiés; le format complet de la base contient sept fichiers préexistants non formatés hors périmètre.
- Parcours navigateur synthétique réel : desktop 1440 px et mobile 390 px sans débordement horizontal; panneau sous le document mobile; survol garde une géométrie stable; reveal clavier/tactile puis Échap; navigation, bascule globale, ajout par sélection, undo/redo; texte long de 80 891 caractères et 3 600 boutons, 1 802 occurrences Alice basculées.
- Essai sémantique Albert avec données uniquement synthétiques : la réponse s’est terminée normalement (`HTTP 200`, `finish_reason=stop`, une tentative) mais a été refusée avec `code=chevauchement_expansion`; le backend a donc interrompu la projection sans exposer les données. Le prompt a depuis été renforcé pour éviter les plages imbriquées. La sortie sémantique du modèle reste non concluante.
- Correctif soumis à revue : les plages globalement étendues sont fusionnées par composantes transitive indépendantes pour le transcript et le contexte. Une catégorie commune est conservée; les catégories qui se heurtent deviennent `donnee_sensible`. Les valeurs, remplacements et pseudonymes proviennent des tranches source finales; aucune nouvelle expansion n’est lancée sur ces unions.
- Tests de correction : expansions `Pierre` / `Pierre Leroy`, chaîne transitive `Pierre Leroy Dupont`, collision inter-catégories avec suffixes entièrement couverts, occurrences qui se recouvrent, répétitions transcript/contexte et confirmation de la projection sans champs temporaires.
- `bash scripts/harness.sh audit` : non requis.

## Décisions

- ADR associée ou « aucune » : aucune.
- Les sources canoniques de relecture sont le transcript après normalisation des en-têtes locuteurs et le contexte original inchangé.
- Les offsets Python sont convertis une seule fois en unités UTF-16 pour le navigateur.
- Les requêtes de confirmation gardent leur schéma et ne transmettent aucun original, plage ou historique.

## Handoff

- État du code : contrôles complets et revue Sol du diff terminés; verdict `REVUE_SOL : OUI`, sans blocage. Le correctif est prêt à être commité et poussé sur la PR brouillon #34.
- Prochaine action : pousser le correctif sur la PR #34 et suivre ses contrôles CI; aucune fusion automatique.
- Risques ou limites : l’essai Albert synthétique initial a révélé le chevauchement; le modèle n’a pas été rappelé après correction. Les tests DeTest valident la fusion déterministe et l’absence de suffixe exposé, sans attester la qualité sémantique Albert après le changement.

## Revue indépendante

- Diff examiné : correctif de fusion transitive non commité sur `feature/relecture-pseudonymisation`.
- Critères vérifiés : fusion source sans perte, catégories conflictuelles conservatrices, projection finale, confirmation sans métadonnées temporaires et contrôles complets.
- Remarques : test facultatif futur pour isoler l’harmonisation d’une même valeur finale observée dans plusieurs champs; l’implémentation harmonise déjà ces catégories globalement.
- Verdict : `REVUE_SOL : OUI`, sans blocage.
