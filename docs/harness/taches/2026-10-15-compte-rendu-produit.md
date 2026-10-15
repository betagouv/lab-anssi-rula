# Tâche : améliorer le compte rendu des entretiens produit

Statut : prêt pour revue technique; validation de qualité réelle non satisfaite

## Objectif

Présenter les analyses de transcripts produit comme un compte rendu UX senior, hiérarchisé, sourcé et directement exploitable, tout en conservant les analyses BizDev et les résultats historiques.

## Périmètre

- Inclus : prompt produit, schéma et validation des réponses/citations, versionnement produit indépendant, persistance des fonctionnalités explicitement étayées, rendu UI et tests.
- Exclu : BizDev, migration SQL, retraitement ou relance de données existantes, export, suppression et déploiement.

## Critères d’acceptation

- [x] Le contrat expose contexte anonymisé, ouverture, profil, points clés, sujets hiérarchisés, enseignements typés et sourcés, pistes prudentes et prochaines étapes sourcées.
- [x] Le JSON produit est strict et validé récursivement; les références sont bornées aux tours transmis et les verbatims reconstruits exactement.
- [x] Les fonctionnalités extraites sont distinctes des pistes analyste et exigent une référence utilisateur.
- [x] Le versionnement produit (`produit-v1`, `produit-v7`) est indépendant de BizDev (`pdf-v1`, `bizdev-v6`).
- [x] L’UI rend le nouveau rapport et conserve le rendu BizDev et ancien produit.
- [x] Les tests DeTest couvrent schéma, natures et origines invalides, références, fonctionnalités, BizDev et fallback UI.
- [ ] L’évaluation réelle démontre une qualité suffisante : les sorties échantillonnées contiennent encore des preuves fragmentaires et des inférences non étayées.

## Plan

1. Adapter le contrat privé produit, sa validation et ses versions sans changer BizDev.
2. Réécrire le prompt et adapter l’affichage du nouveau format avec fallback historique.
3. Ajouter les tests métier et d’interface, puis exécuter le harness complet.
4. Évaluer éphémèrement une source déjà confirmée seulement après vérification locale de son anonymisation; ne rien persister.
5. Préparer le commit et transmettre le diff intégré à la revue Sol avant toute PR.

## Validation

- `bash scripts/harness.sh complet --cible backend` : réussi; Ruff et mypy passent, 325 tests passés et 2 intégrations ignorées car leurs dépendances externes ne sont pas configurées.
- `bash scripts/harness.sh complet --cible frontend` : réussi; 84 tests, svelte-check, TypeScript, ESLint, Prettier et build Vite. Les contrôles ont également été relancés pour la correction du contrat public dans le rendu.
- Contrôles frontend directs après correction de l’affichage : `pnpm test -- --run src/transcripts/ResultatAnalyse.test.ts` (3 tests), `pnpm svelte:check` et `pnpm exec tsc --noEmit` réussis. Le profil complet harness précédent a passé le build et les checks; tests UI ciblés exécutés après correction.
- `git diff --check` : réussi.
- Revue visuelle : aperçu synthétique (non persisté) vérifié en mobile 390×844 et desktop 1280×900. Citations d’enseignement et étape avec locuteur/tour visibles; largeur document mobile 375 px pour viewport 390 px, sans débordement. Les rendus ancien produit et BizDev restent disponibles.
- Évaluation réelle conservée hors dépôt dans un fichier privé : source déjà confirmée id 26, lue en GET; classification préservée. Appel medium, 59,432 s, schéma `produit-v1`/prompt `produit-v7`, modèle `openai/gpt-oss-120b`, effort configuré `medium`, budget 16 384. Sortie valide au schéma, mais qualité non acceptable : références souvent réduites à des fragments, certaines pistes infèrent une demande, et formations/légalités sont attribuées sans preuves claires. Aucun transcript ou verbatim dans le dépôt.
- Diagnostic unique à effort high : échec applicatif `finish_reason_invalide` après environ 90 s. Le diagnostic attaché à l’exception n’a pas été conservé; le `finish_reason` serveur et les tokens sont donc inconnus. L’effort configuré reste inchangé (`medium`). Aucun autre appel n’est prévu dans cette tâche.
- `bash scripts/harness.sh audit` : non requis.

## Décisions

- ADR associée ou « aucune » : aucune.
- Produit : schéma `produit-v1`, prompt `produit-v7`; BizDev conserve `pdf-v1` et `bizdev-v6`.
- Citations reconstruites depuis les références tokenisées; aucune normalisation du verbatim.

## Handoff

- État du code : revue Sol acceptée pour PR brouillon; commit prêt à pousser.
- Prochaine action : pousser la branche et créer la PR brouillon vers `main`, puis suivre les checks CI. Aucun merge ou déploiement n’est autorisé.
- Risques ou limites : la sortie LLM actuelle ne satisfait pas les critères de preuves complètes et d’absence d’invention. L’appel diagnostique high a échoué sans diagnostic précis. Aucune analyse n’a été persistée, aucune source reclassée et aucune donnée n’a été relancée.

## Revue indépendante

- Diff examiné : commit `d6f784e` par Sol.
- Critères vérifiés : contrat public, rétrocompatibilité ancienne/BizDev, tests, références et rendu visuel vérifiés.
- Remarques : P1 de rendu des références corrigé avant cette revue finale. La sortie réelle medium contient encore des références fragmentaires et des inférences non étayées; le diagnostic high finit sur `finish_reason_invalide` sans détail récupérable.
- Verdict : code accepté pour une PR brouillon; qualité réelle bloquante, fusion non approuvée.
