# Tâche : relecture interactive de la pseudonymisation

Statut : correctif de reprise F5 en cours sur la PR brouillon #34

## Objectif

Permettre de relire les occurrences pseudonymisées après préparation d’un transcript et de modifier les masques avant confirmation, avec la source originale disponible uniquement pendant cette préparation temporaire. Reprendre la page et les modifications après F5 tant que le backend conserve la session temporaire.

## Périmètre

- Inclus : modèle d’occurrences source, préparation temporaire, état de relecture accessible au clavier et au tactile, édition des catégories, ajout de masques par sélection, annulation/rétablissement, rôles de locuteurs et prompt partagé Produit/BizDev; reprise de session en mémoire serveur après rechargement.
- Exclu : stockage des originaux, modification des contrats POST/PUT de confirmation, redesign du shell DSFR, changement des analyses historiques.

## Critères d'acceptation

- [x] Les textes source originaux et les plages exactes des occurrences sont fournis dans la seule réponse temporaire de préparation, sans journalisation ni persistance.
- [x] La relecture affiche le document sur environ 75 % de la largeur et le détail du masque sélectionné sur 25 %; le survol révèle temporairement l’original en place sans changement de mise en page, le clic bascule globalement le masque exact.
- [x] Les masques actifs et inactifs restent visibles et cliquables; une occurrence regroupe toutes les mentions identiques exactes dans le transcript et le contexte.
- [x] Le détail du masque sélectionné expose son original en lecture seule, sa catégorie modifiable, son compteur, sa révélation et sa bascule; les catégories et pseudonymes restent cohérents après modification.
- [x] Une sélection de texte propose une catégorie puis attend une action explicite pour créer un masque global exact; un chevauchement partiel incompatible est refusé atomiquement.
- [x] L’ajout depuis la sélection reste dans le panneau latéral, hors du transcript, et reste disponible lorsque le clic extérieur efface la sélection native.
- [x] Annuler et rétablir couvrent ajouts, activations et catégories sans perdre les modifications suivantes.
- [x] Navigation clavier, focus, Échap et commandes tactiles permettent de révéler et parcourir sans dépendre du survol.
- [x] Le POST/PUT de confirmation transmet uniquement le texte projeté et les locuteurs; validation existante, correction des rôles et confirmation sont préservées.
- [x] Les noms de rôles rendus sont `Interne · N`, `Externe · N` et `Indéterminé · N`; les identifiants techniques `SPEAKER_XX` sont conservés.
- [x] Les commandes restent à position fixe pendant que la zone transcript défile jusqu’au masque sélectionné; au clavier aussi, seule cette zone défile.
- [x] Les speakers ont un style distinct, sont renommables en ligne et globalement; leur identifiant technique est conservé et leur libellé ne peut pas être ajouté comme masque.
- [x] La même relecture est utilisée pour Produit et BizDev, avec le prompt partagé mis à jour pour la classification prudente des technologies/produits et la préservation des fonctions professionnelles.
- [x] Les tests métier et la preuve de parcours navigateur couvrent les occurrences globales, collisions, Unicode Python/JavaScript, historique, interactions desktop/mobile et textes longs.
- [x] La préparation est retrouvable par un identifiant non secret en sessionStorage et un cookie `HttpOnly`, `SameSite=Strict`, limité à la route et `Secure` sous HTTPS.
- [x] Les mises à jour structurées restaurent plages, états, catégories, historique, rôles, libellés et métadonnées sans envoyer le texte original ou projeté.
- [x] Les lectures et mutations de préparation sont `no-store`; les mutations vérifient l’origine; les sessions sont isolées et expirent après 30 minutes d’inactivité.
- [x] Confirmation, abandon, expiration et redémarrage du backend effacent ou rendent indisponible le brouillon; l’interface informe avant de quitter avec des changements non synchronisés.
- [ ] Une vérification F5 synthétique confirme la restauration complète sans transcript dans le stockage navigateur, l’URL, les journaux ou la base.

## Plan

1. Étendre le modèle temporaire de préparation avec les sources originales et les occurrences validées.
2. Construire un modèle frontend pur pour les plages, la projection, les pseudonymes stables et l’historique.
3. Intégrer un écran de relecture à la préparation existante et préserver le flux de confirmation.
4. Ajouter les tests DeTest et un scénario navigateur synthétique sans persistance.
5. Ajouter les routes de reprise sécurisées, le stockage RAM glissant et la restauration de l’état éditorial.
6. Exécuter les contrôles requis et pousser sur la PR #34 sans fusion.

## Validation

- Validation finale : `bash scripts/harness.sh complet` passe Ruff, mypy (135 fichiers) et pytest (334 réussis, deux ignorés, couverture globale 99 %), puis échoue au contrôle Svelte WSL car `@rollup/rollup-linux-x64-gnu` manque dans le `node_modules` Windows partagé.
- Contrôles frontend Windows : `pnpm test` (93 tests), `pnpm check`, `pnpm lint:check`, `pnpm format:check` et `pnpm build` passent; `svelte-check` signale zéro erreur et zéro avertissement.
- `uv run ruff format --check` passe sur les fichiers backend modifiés; le format complet de la base contient sept fichiers préexistants non formatés hors périmètre.
- Parcours navigateur synthétique réel : desktop 1440 px et mobile 390 px sans débordement horizontal; panneau sous le document mobile; survol garde une géométrie stable; reveal clavier/tactile puis Échap; navigation, bascule globale, ajout par sélection, undo/redo; texte long de 80 891 caractères et 3 600 boutons, 1 802 occurrences Alice basculées.
- Essai sémantique Albert avec données uniquement synthétiques : la réponse s’est terminée normalement (`HTTP 200`, `finish_reason=stop`, une tentative) mais a été refusée avec `code=chevauchement_expansion`; le backend a donc interrompu la projection sans exposer les données. Le prompt a depuis été renforcé pour éviter les plages imbriquées. La sortie sémantique du modèle reste non concluante.
- Correctif revu et poussé : les plages globalement étendues sont fusionnées par composantes transitive indépendantes pour le transcript et le contexte. Une catégorie commune est conservée; les catégories qui se heurtent deviennent `donnee_sensible`. Les valeurs, remplacements et pseudonymes proviennent des tranches source finales; aucune nouvelle expansion n’est lancée sur ces unions.
- Tests de correction : expansions `Pierre` / `Pierre Leroy`, chaîne transitive `Pierre Leroy Dupont`, collision inter-catégories avec suffixes entièrement couverts, occurrences qui se recouvrent, répétitions transcript/contexte et confirmation de la projection sans champs temporaires.
- `bash scripts/harness.sh audit` : non requis.
- Complément UX desktop navigateur (1440×900) : la barre conserve exactement sa position pendant le défilement interne (`top=196`, `scrollTop=0→2337`); le speaker `Indéterminé · 4` est visuellement distinct et chaque alias global affiche un seul champ en édition.
- Complément UX mobile navigateur (390×844) : panneau sous le transcript, largeur document 375 px pour viewport 390 px; révélation explicite affiche les 3 mentions et `Échap` les masque de nouveau.
- Complément clavier et sérialisation : activation au clavier d’un speaker et d’Occurrence suivante, alias `Alice` sur les 60 mentions, `SPEAKER_04` conservé dans le contenu et les métadonnées, aucun masque sur les identifiants; glisser sur le libellé ne crée pas de sélection caviardable.
- Validation finale après ajout de ces cas : `uv run ruff check .`, `uv run ruff format --check` (trois fichiers backend), `uv run mypy` et `uv run pytest` passent; 334 tests backend passent et deux sont ignorés. `pnpm check`, `pnpm lint:check`, `pnpm format:check`, `pnpm test` (93 tests) et `pnpm build` passent sous Windows. `bash scripts/harness.sh complet` passe les contrôles backend puis échoue au `svelte-check` WSL parce que `@rollup/rollup-linux-x64-gnu` est absent du `node_modules` Windows partagé; le contrôle natif Windows équivalent passe.
- Reprise F5 : TestClient valide le cookie, l’isolation, l’expiration glissante, la suppression, le `no-store`, le refus d’un corps contenant le transcript, et la restauration des modifications complètes; le modèle frontend valide la réhydratation de l’historique. La vérification intégrée du F5 dans un navigateur réel reste à faire.
- Origine de l’upload en développement : Vite ne réécrit plus l’en-tête `Host`; après redémarrage du seul conteneur frontend, une requête `DELETE` de contrôle avec `Origin: http://localhost:5173` a atteint la validation de préparation et renvoyé le `404` attendu sur un identifiant fictif, sans `403 Origine invalide`.
- Correctif de sélection : l’action d’ajout est rendue dans le panneau latéral et la capture ignore une sélection native repliée; `Échap` ou Annuler la ferme. `pnpm test`, `pnpm check`, `pnpm lint:check`, `pnpm format:check` et `pnpm build` passent (93 tests, zéro diagnostic Svelte).
- CI GitHub du code `610a158` : Backend Python, Frontend Svelte, CodeQL, Analyze (actions, JavaScript/TypeScript, Python) et GitGuardian passent.

## Décisions

- ADR associée ou « aucune » : aucune.
- Les sources canoniques de relecture sont le transcript après normalisation des en-têtes locuteurs et le contexte original inchangé.
- Les offsets Python sont convertis une seule fois en unités UTF-16 pour le navigateur.
- Les requêtes de confirmation gardent leur schéma et ne transmettent aucun original, plage ou historique.

## Handoff

- État du code : commit `6a59577` poussé sur `feature/relecture-pseudonymisation`; PR #34 mise à jour, ouverte en brouillon et non fusionnée. Le harness backend passe; ses contrôles frontend WSL échouent sur la dépendance Rollup Linux manquante, alors que tous les contrôles frontend Windows passent.
- Prochaine action : revue humaine de la PR; aucune fusion automatique.
- Risques ou limites : la reprise après F5 est couverte par les tests API et modèle, mais son parcours complet n’a pas été rejoué dans un navigateur. L’essai Albert synthétique initial a révélé le chevauchement; le modèle n’a pas été rappelé après correction. Les tests DeTest valident la fusion déterministe et l’absence de suffixe exposé, sans attester la qualité sémantique Albert après le changement.

## Revue indépendante

- Diff examiné : correctif de fusion transitive commité `a63759e` sur `feature/relecture-pseudonymisation`.
- Critères vérifiés : fusion source sans perte, catégories conflictuelles conservatrices, projection finale, confirmation sans métadonnées temporaires et contrôles complets.
- Remarques : test facultatif futur pour isoler l’harmonisation d’une même valeur finale observée dans plusieurs champs; l’implémentation harmonise déjà ces catégories globalement.
- Verdict : `REVUE_SOL : OUI`, sans blocage.
