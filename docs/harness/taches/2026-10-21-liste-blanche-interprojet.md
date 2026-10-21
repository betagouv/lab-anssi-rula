# Tâche : liste blanche partagée entre produits

Statut : prête pour revue

## Objectif

Permettre aux utilisateurs de gérer les termes qui doivent rester visibles dans les prochaines préparations PDF MSS et MSC, tout en améliorant le prompt de pseudonymisation.

## Périmètre

- Inclus : page CRUD « Liste blanche » accessible depuis l’accueil et l’en-tête; persistance partagée PostgreSQL; termes initiaux MSS/Mon Service Sécurisé/LAB/Laboratoire d’innovation de l’ANSSI/ANSI/Annecy; validation et unicité Unicode; gestion optimiste des modifications concurrentes; filtre local des masques proposés par Albert; précision des consignes du prompt.
- Exclu : envoi de la liste à Albert, recalcul des brouillons déjà préparés ou des transcripts confirmés, retrait des masques explicitement ajoutés en relecture.

## Critères d'acceptation

- [x] La liste partagée se consulte et se modifie depuis la page dédiée; les créations, éditions et suppressions détectent les conflits de révision.
- [x] La migration 003 crée la table et insère les six termes initiaux une seule fois; une suppression de seed reste effective après relance du runner.
- [x] La clé d’unicité est trim + espaces comprimés + NFC + casefold; valeur vide, ponctuation seule, dépassement de longueur et doublon normalisé sont refusés.
- [x] Le filtre local intervient après réception et fusion/expansion des propositions Albert, avant attribution des pseudonymes, occurrences et contenu; il préserve les offsets source pour Unicode, frontières, espaces et apostrophes.
- [x] Un masque englobant est soustrait autour des termes autorisés sans exposer ses portions sensibles; les résidus contenant lettres/chiffres conservent leurs symboles; les seuls fragments supprimés sont entièrement composés d’espaces/ponctuation.
- [x] Les termes de liste ne sont ajoutés à aucun message, schéma ou retry Albert; le prompt exclut les segments génériques isolés, mais conserve ces mots dans une expression sensible complète.
- [x] Les préparations sauvegardées ne sont pas recalculées et la relecture humaine reste souveraine.
- [x] `bash scripts/harness.sh complet` intégralement vert depuis un cwd WSL stable sous Node 24.13.0.

## Plan

1. Ajouter la migration 003, le domaine, les dépôts mémoire/PostgreSQL, le service et les routes avec contrôle optimiste des révisions.
2. Construire la page dédiée et ses entrées depuis l’accueil et l’en-tête.
3. Ajouter la comparaison Unicode avec projection sur offsets originaux, puis soustraire les plages autorisées après fusion des propositions.
4. Ajuster le prompt sans seeds; ajouter les tests métier, API, concurrence, confidentialité et régression du flux.
5. Exécuter le harness complet, documenter les preuves et demander la revue Sol finale.

## Validation

- `uv run ruff check src tests` : réussi.
- `uv run ruff format --check src tests` : réussi.
- `uv run mypy` : réussi, 63 modules.
- `uv run pytest tests/api/test_liste_blanche.py tests/test_liste_blanche.py tests/test_transcripts_pdf_liste_blanche.py -q` : 20 passés après corrections de revue Sol.
- Base PostgreSQL jetable `pgvector/pgvector:pg17`, port local 55432, supprimée après chaque exécution; `RULA_TEST_DATABASE_URL=postgresql://postgres:local-only-test@127.0.0.1:55432/postgres uv run pytest tests/test_migrations.py -q` : 4 passés. Couvre base vide, base existante, filtres de conservation, identité/contenu/dates/locuteurs, idempotence, suppression d’un seed, rollback et unicité/révisions du dépôt.
- `bash -lc 'cd /mnt/c/Users/pleroy/.codex/worktrees/liste-blanche-interprojet/RULA && bash scripts/harness.sh complet'` : code de sortie 0 sous Node 24.13.0; Ruff et mypy réussis; pytest 122 passés, 4 ignorés (base de migration sans DSN), 1 avertissement; svelte-check 0 erreur/avertissement; Vitest 38/38; `pnpm check`, `pnpm lint:check`, `pnpm format:check` et `pnpm build` réussis. ESLint prend environ 2 min 30 sur le montage `/mnt/c`, sans erreur. Le node_modules Linux était isolé dans ce worktree.
- Commandes UI exécutées sous PowerShell depuis `ui` : `pnpm lint:check`, `pnpm format:check`, `pnpm svelte:check`, `pnpm test`, `pnpm build`. Résultat final après correction du test SSR whitespace : lint et format réussis, Svelte 0 erreur/avertissement, 38 tests passés, build Vite réussi. Le node_modules Windows initial était isolé dans ce worktree.
- `git diff --check` : réussi avant le dernier ajout de preuve; à relancer avant commit.
- `bash scripts/harness.sh audit` : non exécuté, profil non requis.

## Décisions

- ADR associée : aucune; contrat cadré par la revue Sol architecture.
- Revue Sol finale : validée, aucun constat actionnable restant après corrections des résidus ponctués et de la composition Hangul LV+T.
- Limite : la liste réduit les masques proposés automatiquement mais ne garantit pas l’absence de toute donnée personnelle; l’utilisateur peut réactiver ou ajouter des masques en relecture.

## Handoff

- État du code : implémentation, revue Sol et harness complet terminés dans le worktree `codex/liste-blanche-interprojet`; aucun changement produit dans le checkout parent et aucun déploiement.
- Prochaine action : relancer `git diff --check`, commit GPG signé, push et ouverture de la PR autorisée; attendre ses checks CI.
- Risques ou limites : une erreur d’offset ou de soustraction peut exposer une valeur sensible; les intervalles sont projetés sur le texte original et testés exactement. La liste réduit les masques proposés automatiquement mais ne garantit pas l’absence de toute donnée personnelle; l’utilisateur peut réactiver ou ajouter des masques en relecture.

## Revue indépendante

- Diff examiné : Sol a demandé des corrections confidentialité/Unicode concernant la conservation de symboles alphanumériques et la composition Hangul; corrections et tests de régression validés.
- Critères vérifiés : couverture automatisée selon les preuves ci-dessus.
- Remarques : le comportement de matching Unicode et de soustraction est testé; aucun constat actionnable restant.
- Verdict : accepté.
