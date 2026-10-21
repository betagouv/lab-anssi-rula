# RULA

RULA permet de pseudonymiser des transcripts PDF d’entretiens Produit ou BizDev pour MSS et MSC. Le PDF source reste temporaire; seul le transcript confirmé est conservé.

## Démarrer

Installer Python 3.13, `uv`, Node.js, `pnpm`, Bash et Docker. Copier `.env.template` vers `.env`, puis renseigner les paramètres PostgreSQL et Albert.

```bash
uv sync
cd ui && pnpm install
cd ..
docker compose up --build
```

L’interface de développement est disponible à `http://localhost:5173` et l’API à `http://localhost:3001`.

## Vérifier

```bash
bash scripts/harness.sh complet
bash scripts/harness.sh audit
```

## Migration de la base active

La migration `002_pseudonymisation_seule.sql` supprime les données et tables hors parcours. Elle ne conserve que les produits MSS/MSC et les transcripts confirmés de type `produit` ou `bizdev` associés à ces produits. Elle préserve les identifiants des lignes conservées. Une ligne confirmée d’un autre type ne sera pas conservée.

Le hook `scripts/clever-cloud/post-build-clever.sh` applique la migration pendant le build, avant le démarrage du nouveau runtime. Une bascule de base active doit donc être planifiée en maintenance : arrêter les anciennes instances avant le build, prendre la sauvegarde opérationnelle requise, exécuter le build, puis vérifier `GET /api/sante`, la migration enregistrée, MSS/MSC et les sources conservées. En cas d’échec, restaurer la sauvegarde avant de relancer l’application. Aucun déploiement n’est effectué par cette PR. Les sauvegardes Clever Cloud restent hors périmètre.

Voir [l’architecture](docs/architecture.md), [la décision ADR 0004](docs/adr/0004-pseudonymisation-seule.md) et [la procédure de déploiement](docs/deploiement-clever-cloud.md).
