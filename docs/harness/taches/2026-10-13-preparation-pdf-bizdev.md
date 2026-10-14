# Tâche : Fiabiliser les préparations PDF BizDev volumineuses

Statut : prête à revoir

## Objectif

Réduire la taille du message de fragments envoyé à Albert et rendre les échecs terminaux diagnostiquables sans exposer le jeton ni le contenu du transcript.

## Périmètre

- Inclus : sérialisation compacte des fragments et tokens, journalisation terminale sûre, timeout de 180 s indépendant pour chaque tentative HTTP, une reprise uniquement sur coupure réseau transitoire explicitement identifiée, message de timeout explicite et tests des invariants.
- Exclu : changement de modèle, budget de sortie, validation des réponses ou durée de conservation. Le rejeu diagnostique valide uniquement le service de préparation; aucune confirmation humaine ni écriture en base n'a été effectuée.

## Critères d’acceptation

- [x] Les paires de tokens conservent les index et textes exacts, avec JSON compact.
- [x] Les échecs terminaux indiquent la phase, le type d’exception et une empreinte tronquée du jeton; aucune exception arbitraire ni donnée source n’est journalisée.
- [x] Les remplacements validés restent identiques dans les tests; les contrôles complets passent.
- [x] Une seule reprise est permise pour `RemoteProtocolError`, `ReadError` ou `ConnectError`; les états partiels sont remis à zéro et chaque tentative reçoit son propre délai de 180 s.
- [x] Le timeout expose le message exact « L'API Albert n'a pas répondu dans le délai imparti. » à l'interface; les logs terminal et par groupe donnent des métadonnées sûres.

## Plan

1. Compacter la représentation transmise et adapter les adaptateurs de test.
2. Journaliser les métadonnées sûres des échecs terminaux.
3. Valider les tests ciblés, le harness complet et l’audit.
4. Vérifier la reprise avec un serveur HTTP loopback réel qui coupe un flux SSE, sans mock ni monkey-patching.

## Validation

- Commandes ciblées pendant l’itération : `uv run ruff check src/transcripts_pdf/service.py src/api/transcripts_pdf.py tests/test_transcripts_pdf.py tests/api/test_transcripts_pdf.py`; `uv run pytest tests/test_transcripts_pdf.py tests/api/test_transcripts_pdf.py -q` — 74 passed.
- `bash scripts/harness.sh complet` avant le timeout distinct : code 0; Ruff et mypy OK, 295 passed / 2 skipped, Svelte 0 erreur/avertissement, Vitest 80/80, `pnpm check`, lint, format et build OK.
- Après ajout du timeout : Ruff et mypy OK, `uv run pytest -q` — 296 passed / 2 skipped.
- Avant l'ajustement demandé du délai : `uv run ruff check src/ tests/`, `uv run mypy`, `uv run pytest -q` — OK, 301 passed / 2 skipped; l'intégration loopback couvrait cinq scénarios. Ces résultats ne valident pas la révision actuelle.
- `bash scripts/harness.sh audit` : code 0; 12 constats non bloquants (smells/Bandit).
- Après le changement vers 180 s par tentative et ajout du cas SSE actif, une relance du profil complet a produit des sorties réussies pour chaque étape : Ruff, mypy, 304 tests backend (2 ignorés), Svelte-check (0 erreur/avertissement), Vitest (81 tests), TypeScript, ESLint, Prettier et build Vite. La session shell globale n'a pas rendu son code de sortie après le build. Une exécution précédente s'était arrêtée au contrôle Prettier après le changement du test frontend; le formatage a été corrigé avant cette relance.

La source diagnostique compte 19 pages, 62 415 caractères extraits, 158 fragments et 36 groupes. Pour le groupe 16 (2 000 caractères, 411 tokens, 1 locuteur), le JSON de fragments passe de 17 629 à 7 344 caractères; le message complet passe de 17 653 à 7 368 caractères. Le rejeu unique du groupe 16 avec `openai/gpt-oss-120b`, effort `high` et délai 180 s réussit en 98,7 s : 7 400 événements, `finish_reason=stop`, 334 tokens de réponse, 1 locuteur et 9 remplacements validés.

Le rejeu complet avec parallélisme effectif 7 échoue à 8/36 après 246 s par `DelaiAlbertDepasse`. Un rejeu complet borné à 4 (effectif 3, car le même pool exécutait l’orchestration et les groupes) échoue à 15/36 après 901,5 s, également par `DelaiAlbertDepasse`. Aucun texte, réponse brute ni message d’exception n’a été persisté.

À cette étape, un rejeu avec délai total de 360 s par appel et pool de groupes distinct à 8 s’est arrêté à 15/36 après 233,7 s. Le premier groupe en échec identifié était le 17, phase `appel_albert`, `ErreurCommunicationAlbert`, HTTP 200, 3 099 événements, 12 543 caractères de raisonnement, aucun premier contenu, aucune raison de fin et zéro caractère de contenu. La cause réseau sous-jacente n’avait pas été capturée et les groupes actifs avaient été annulés. D’autres groupes réussis avaient pris jusqu’à 187,790 s. À ce stade, la réussite complète et la fusion n’étaient pas validées.

Les tests d'intégration historiques confirmaient le partage du délai total avant son remplacement par un délai indépendant par tentative. Les tests actuels vérifient la reprise unique après coupure, la remise à zéro des données partielles, l'absence de reprise après une erreur HTTP ou une réponse invalide, ainsi que les délais indépendants par tentative et entre appels. Le flux SSE actif est également interrompu à l'échéance.

Sous l'ancienne configuration à 360 s partagés par tentative logique, un rejeu complet a terminé les 36/36 groupes, la fusion et la finalisation en 385,1 s; un groupe a pris 219,055 s. Ce résultat historique ne prouvait pas la réussite sous le délai désormais appliqué indépendamment à chaque tentative. Le 2026-10-14, le POST multipart réel de la route d'import a accepté le PDF avec HTTP 202, puis la préparation avec Albert réel a terminé les 36/36 groupes, la fusion et la finalisation en 198,3 s avec la configuration de 180 s par tentative. Le résultat en mémoire comptait 5 locuteurs, 124 remplacements et 64 822 caractères préparés. Aucune confirmation ni écriture en base n'a eu lieu; le processus de test a été arrêté après vérification et aucun texte brut, réponse Albert ou donnée d'identité n'a été imprimé ou persisté.

## Décisions

- ADR associée : `docs/adr/0003-transcripts-pdf.md`.

## Handoff

- État du code : sérialisation compacte, journalisation terminale sûre, délai indépendant de 180 s par tentative, message public explicite et reprise réseau strictement bornée en place. Les contrôles CI sont verts et le rejeu réel du PDF termine les 36 groupes sous le contrat actuel.
- Prochaine action : fusionner la PR 31 après la PR 30, puis déployer DEMO par l'action GitHub dédiée.
- Risques ou limites : le rejeu complet antérieur utilisait l'ancien délai à 360 s et ne prouve pas la réussite avec 180 s par tentative. Un gros document peut désormais échouer et remonter le message public dédié.

## Revue indépendante

- Diff examiné : changement final de la préparation PDF, y compris délai indépendant par tentative, diagnostics terminal/par groupe et message public.
- Critères vérifiés : compactage, reprises réseau bornées, timeout par tentative, interruption d'un SSE actif, propagation du message exact et métadonnées sans contenu privé; profil backend/frontend vérifié par sorties individuelles réussies.
- Remarques : le rejeu réel Albert/PDF a été effectué après la revue et confirme le parcours complet sans modification du code.
- Verdict : accepté par Sol pour mise à jour de la PR; aucune fusion ni aucun déploiement autorisé.
