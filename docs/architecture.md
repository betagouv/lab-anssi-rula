# Architecture de RULA

RULA sert à pseudonymiser des transcripts PDF avant de conserver leur contenu. L’application propose MSS (MonServiceSécurisé) et MSC (MesServicesCyber), avec une liste séparée par produit. Les PDF de type Produit et BizDev suivent le même parcours de pseudonymisation.

## Services

Docker Compose orchestre PostgreSQL, le backend FastAPI et le frontend Svelte 5 avec Vite. Le frontend appelle `/api/*`; Vite relaie ces appels au backend. En production, le backend sert les fichiers compilés du frontend.

Le backend extrait le texte natif des PDF, sans OCR. Le PDF original et le brouillon non confirmé restent temporaires. La préparation Albert expose sa progression; la relecture peut corriger les six catégories de pseudonymisation et les locuteurs. La confirmation explicite enregistre uniquement la source pseudonymisée. L’historique permet de consulter, télécharger en PDF et supprimer les sources confirmées.

Les analyses, projets de recherche, imports FeatureBase et retours BizDev tabulaires ne font pas partie de l’application. Le type BizDev ne désigne que la provenance d’un transcript PDF pseudonymisé.

## Données

Les seules tables applicatives sont `produits` et `transcripts`. Les produits conservés sont MSS et MSC. Un transcript conserve son identifiant, son produit, son nom de fichier, son type (`produit` ou `bizdev`), sa date, son contenu pseudonymisé, son contexte pseudonymisé, ses locuteurs, son état de confirmation et ses dates de création/modification.

La migration `001_schema_unifie.sql` est conservée pour préserver l’historique de migration. La migration versionnée `002_pseudonymisation_seule.sql` réduit une base existante au nouveau schéma et ne garde que les lignes confirmées de type Produit/BizDev rattachées à MSS ou MSC. Sur une base vide, le runner exécute `001`, puis `002`. Le runner enregistre chaque migration dans `migrations_executees` dans la même transaction que son SQL.

La préparation en mémoire est reliée au navigateur par un identifiant et un cookie `HttpOnly`, `SameSite=Strict`; les réponses de préparation interdisent le cache et les mutations valident l’origine. Une préparation expirée ou interrompue doit être réimportée.

## Configuration

Toute configuration est lue par `charge_configuration()`. Les variables nécessaires sont les identifiants PostgreSQL, l’URL et la clé API Albert, le modèle Albert, les limites de préparation et les paramètres du serveur RULA. `.env.template` fournit les noms et valeurs locales par défaut.

## Démarrage local

```bash
uv sync
cd ui && pnpm install
docker compose up --build
```

Le frontend de développement est disponible sur `http://localhost:5173`; l’API est sur `http://localhost:3001`.

## Migration et exploitation

Le hook Clever Cloud `scripts/clever-cloud/post-build-clever.sh` exécute les migrations avant le démarrage du nouveau runtime. La migration `002` est destructive pour les données hors périmètre. Avant de lancer un build sur une base active, l’exploitation doit coordonner une fenêtre de maintenance, arrêter les anciennes instances et réaliser la sauvegarde opérationnelle applicable. Après le build, vérifier la version de migration, MSS/MSC, les lignes conservées et l’endpoint de santé. En cas d’échec, restaurer la sauvegarde avant de relancer l’application. Les sauvegardes Clever Cloud ne sont pas modifiées par cette migration.

Les détails de préparation et de vérification de la bascule sont dans [la procédure Clever Cloud](deploiement-clever-cloud.md). La décision durable est documentée dans [ADR 0004](adr/0004-pseudonymisation-seule.md).
