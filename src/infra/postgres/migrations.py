from pathlib import Path

import psycopg2

from configuration import BaseDeDonnees


REPERTOIRE_MIGRATIONS = Path(__file__).resolve().parents[3] / "migrations"
VERROU_MIGRATIONS = 987654321


def execute_migrations(
    config: BaseDeDonnees, repertoire: Path = REPERTOIRE_MIGRATIONS
) -> list[str]:
    executees: list[str] = []
    with psycopg2.connect(
        host=config.hote,
        dbname=config.nom,
        user=config.utilisateur,
        password=config.mot_de_passe,
        port=config.port,
    ) as connexion:
        with connexion.cursor() as curseur:
            curseur.execute("SELECT pg_advisory_xact_lock(%s)", (VERROU_MIGRATIONS,))
            curseur.execute(
                """CREATE TABLE IF NOT EXISTS migrations_executees (
                    nom TEXT PRIMARY KEY,
                    executee_le TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )"""
            )
            for chemin in sorted(repertoire.glob("*.sql")):
                curseur.execute(
                    "SELECT 1 FROM migrations_executees WHERE nom = %s", (chemin.name,)
                )
                if curseur.fetchone() is not None:
                    continue
                curseur.execute(chemin.read_text(encoding="utf-8"))
                curseur.execute(
                    "INSERT INTO migrations_executees (nom) VALUES (%s)", (chemin.name,)
                )
                executees.append(chemin.name)
    return executees
