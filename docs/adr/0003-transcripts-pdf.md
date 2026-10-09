# ADR 0003 — Importer et analyser des transcripts PDF

Statut : accepté

## Contexte

Les entretiens utilisateurs et retours BizDev arrivent parfois en PDF, alors que RULA sait déjà gérer des transcripts texte et des sources produit. Ces documents peuvent contenir des données personnelles ou sensibles et doivent être relus avant leur analyse. Les traitements LLM s’effectuent par Albert et les analyses de projet reposent déjà sur des étapes validables.

## Décision

Le backend extrait uniquement le texte PDF natif, sans OCR. Le fichier et le texte d’origine restent éphémères. Un service d’anonymisation propose des remplacements structurés et normalise les locuteurs; la préparation est éditable par une personne avant confirmation. Seul le texte anonymisé, le contexte anonymisé, les locuteurs pseudonymisés, le type et la date de source sont conservés.

Les analyses emploient des schémas distincts selon la source. Les citations sont vérifiées contre les tours conservés. Les sources confirmées contribuent aux analyses du périmètre autorisé. Les tâches d’analyse sont persistantes et rattachées à une révision du corpus afin de reprendre un travail interrompu et d’écarter tout résultat obsolète.

La préparation découpe les tours et le contexte en fragments puis les regroupe sous une limite de 2 000 caractères par appel; les tours longs sont fragmentés avec leurs identifiants de tour et de locuteur. Les valeurs détectées sont résolues uniquement dans le fragment transmis, puis dédupliquées et fusionnées en mémoire avant le remplacement exact dans les champs originaux. Valeur absente, catégorie contradictoire ou chevauchement incompatible invalide la préparation. La synthèse et les citations restent une analyse unique du texte anonymisé complet. Les appels sont séquentiels et s’arrêtent au premier échec. La préparation est asynchrone côté API, avec état temporaire en mémoire et expiration; un redémarrage exige un nouvel envoi.

Le schéma de données est livré par une migration unique versionnée. Elle ne supprime que les objets applicatifs RULA, conserve le registre du runner et son verrou transactionnel, et peut être rejouée sans effacer les données après son initialisation.

## Validation et limite connue

Le Harness complet passe : 235 tests backend, couverture 100 %, 56 tests frontend, Svelte, lint, format et build. Les deux interleavings PostgreSQL des sauvegardes obsolètes passent sur la base isolée. Le démarrage Compose utilise un volume de projet séparé; la vérification du menu a nécessité un redémarrage du conteneur Vite après modification du bind Windows. Sur Albert réel, un groupe représentatif passe, mais un groupe de 2 000 caractères a renvoyé 504; son unique essai SSE a reçu HTTP 200 sans contenu ni événement final avant le délai global. La préparation réelle complète reste donc non qualifiée. Aucun appel de diagnostic additionnel n’est prévu.

## Conséquences

- Les PDF sans texte natif, chiffrés ou hors limites sont refusés explicitement; aucun contenu n’est tronqué.
- Toute nouvelle source PDF exige une validation humaine avant analyse.
- Toute modification d’une source confirmée invalide ses analyses et les résultats dérivés du corpus concerné.
- La migration initiale efface les données applicatives d’un ancien schéma; la bascule doit être planifiée par l’exploitation avant exécution.
