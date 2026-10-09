# ADR 0003 — Importer et analyser des transcripts PDF

Statut : accepté

## Contexte

Les entretiens utilisateurs et retours BizDev arrivent parfois en PDF, alors que RULA sait déjà gérer des transcripts texte et des sources produit. Ces documents peuvent contenir des données personnelles ou sensibles et doivent être relus avant leur analyse. Les traitements LLM s’effectuent par Albert et les analyses de projet reposent déjà sur des étapes validables.

## Décision

Le backend extrait uniquement le texte PDF natif, sans OCR. Le fichier et le texte d’origine restent éphémères. Un service d’anonymisation propose des remplacements structurés et normalise les locuteurs; la préparation est éditable par une personne avant confirmation. Seul le texte anonymisé, le contexte anonymisé, les locuteurs pseudonymisés, le type et la date de source sont conservés.

Les analyses emploient des schémas distincts selon la source. Les citations sont vérifiées contre les tours conservés. Les sources confirmées contribuent aux analyses du périmètre autorisé. Les tâches d’analyse sont persistantes et rattachées à une révision du corpus afin de reprendre un travail interrompu et d’écarter tout résultat obsolète.

La préparation découpe les tours et le contexte en fragments puis les regroupe sous une limite de 2 000 caractères source par appel; les tours longs sont fragmentés avec leurs identifiants de tour et de locuteur. Chaque fragment transmis contient une tokenisation avec IDs explicites. Le modèle renvoie des plages de tokens inclusives; Python résout les plages exclusivement dans le fragment identifié, puis vérifie les slices source avant déduplication et remplacement exact en mémoire. Aucune valeur textuelle proposée par le modèle n’est utilisée comme plage de remplacement. Valeur absente, ID hors fragment, catégorie contradictoire ou chevauchement incompatible invalide la préparation. Le prompt d’anonymisation version 2 traite le transcript comme donnée non fiable et demande d’ignorer les instructions transcrites. La synthèse et les citations restent une analyse unique du texte anonymisé complet. Les appels de préparation partagent un pool borné global par processus, réglé par `ALBERT_PARALLELISME_ANONYMISATION` (valeur positive, défaut 8); chaque groupe utilise un adaptateur indépendant et les réponses sont réassemblées dans l’ordre source. Au premier échec, la file est annulée, les appels actifs sont drainés et aucun résultat partiel n’est retourné. La préparation est asynchrone côté API, avec état temporaire en mémoire et expiration; un redémarrage exige un nouvel envoi.

Le schéma de données est livré par une migration unique versionnée. Elle ne supprime que les objets applicatifs RULA, conserve le registre du runner et son verrou transactionnel, et peut être rejouée sans effacer les données après son initialisation.

## Validation et limite connue

Le Harness backend en conteneur jetable compte 267 tests, deux intégrations PostgreSQL ignorées par défaut, couverture 100 %, Ruff et mypy réussis. Le frontend compte 60 tests, avec Svelte-check, ESLint et Prettier réussis. Les tests de parallélisation vérifient le plafond global, l’ordre stable, l’isolation des adaptateurs, l’annulation et la progression. L’E2E produit synthétique couvre une préparation PDF native, validation, analyse avec références, scan, trois étapes de projet et analyse transverse; le parcours BizDev couvre la préparation, validation, analyse référencée et provenance sans projet. La transverse a retourné 2 besoins produit et 3 BizDev. Un job d’analyse en attente a été repris au démarrage sans nouveau POST après séparation entre factory FastAPI à injection et factory concrète du worker.

Le modèle est `openai/gpt-oss-120b`. La préparation utilise `high`, JSON Schema strict, 16 384 tokens maximum, `temperature=1` et `top_p=1`. Un PDF réel a été préparé entièrement avec 18 groupes et 58 remplacements, mais son aperçu n’a pas été validé par une personne; son analyse est donc non exécutée. Aucun PDF binaire n’est transmis à Albert.

La préparation en cours vit en mémoire. Une copie de tests dans `/app` a déclenché Uvicorn `--reload` et effacé un jeton actif; l’utilisateur a été informé et devra réimporter ce fichier. Ne pas exécuter de tests dans le conteneur surveillé. La suppression de `--reload` et le TTL calculé après la fin de préparation restent à appliquer quand aucun upload n’est actif.

## Conséquences

- Les PDF sans texte natif, chiffrés ou hors limites sont refusés explicitement; aucun contenu n’est tronqué.
- Toute nouvelle source PDF exige une validation humaine avant analyse.
- Toute modification d’une source confirmée invalide ses analyses et les résultats dérivés du corpus concerné.
- La migration initiale efface les données applicatives d’un ancien schéma; la bascule doit être planifiée par l’exploitation avant exécution.


## Préparation en parallèle

L’anonymisation traite jusqu’à huit groupes simultanément par processus, réglé par `ALBERT_PARALLELISME_ANONYMISATION` (valeur positive, défaut 8). Toutes les préparations partagent le même pool ; chaque groupe crée son propre adaptateur Albert pour isoler les métriques. Les résultats sont réassemblés selon l’ordre source. Au premier échec, les groupes en file sont annulés, les appels déjà lancés sont drainés puis ignorés, et aucun résultat partiel n’est retourné. La progression expose la liste triée des groupes en cours et ne devient terminale qu’après ce drainage.
