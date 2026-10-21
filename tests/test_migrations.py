from pathlib import Path
from uuid import uuid4
import os

import psycopg2
from psycopg2 import sql
import pytest

from configuration import BaseDeDonnees
from infra.postgres.migrations import execute_migrations


@pytest.fixture
def base_temporaire(tmp_path: Path):
    dsn = os.getenv("RULA_TEST_DATABASE_URL")
    if not dsn:
        pytest.skip("RULA_TEST_DATABASE_URL must point to disposable PostgreSQL")
    admin = psycopg2.connect(dsn)
    admin.autocommit = True
    nom = f"rula_test_{uuid4().hex}"
    with admin.cursor() as curseur:
        curseur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(nom)))
    parametres = psycopg2.extensions.parse_dsn(dsn)
    config = BaseDeDonnees(
        parametres["host"],
        int(parametres.get("port", 5432)),
        nom,
        parametres["user"],
        parametres["password"],
    )
    try:
        yield config
    finally:
        admin.cursor().execute(
            sql.SQL("DROP DATABASE IF EXISTS {} WITH (FORCE)").format(
                sql.Identifier(nom)
            )
        )
        admin.close()


def _verifier(config: BaseDeDonnees, requete: str):
    with (
        psycopg2.connect(
            host=config.hote,
            port=config.port,
            dbname=config.nom,
            user=config.utilisateur,
            password=config.mot_de_passe,
        ) as connexion,
        connexion.cursor() as curseur,
    ):
        curseur.execute(requete)
        return curseur.fetchall()


def test_migrations_vide_et_relance_idempotente(base_temporaire: BaseDeDonnees) -> None:
    repertoire = Path(__file__).parents[1] / "migrations"
    assert execute_migrations(base_temporaire, repertoire) == [
        "001_schema_unifie.sql",
        "002_pseudonymisation_seule.sql",
    ]
    assert execute_migrations(base_temporaire, repertoire) == []
    assert _verifier(base_temporaire, "SELECT nom FROM produits ORDER BY nom") == [
        ("MSC",),
        ("MSS",),
    ]
    assert _verifier(base_temporaire, "SELECT count(*) FROM transcripts")[0][0] == 0


def test_migration_preserve_transcript_confirme_et_ses_identifiants(
    base_temporaire: BaseDeDonnees, tmp_path: Path
) -> None:
    migrations = Path(__file__).parents[1] / "migrations"
    premiere = tmp_path / "premiere"
    premiere.mkdir()
    (premiere / "001_schema_unifie.sql").write_text(
        (migrations / "001_schema_unifie.sql").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    execute_migrations(base_temporaire, premiere)
    with (
        psycopg2.connect(
            host=base_temporaire.hote,
            port=base_temporaire.port,
            dbname=base_temporaire.nom,
            user=base_temporaire.utilisateur,
            password=base_temporaire.mot_de_passe,
        ) as connexion,
        connexion.cursor() as curseur,
    ):
        curseur.execute("SELECT id FROM produits WHERE nom = 'MSS'")
        ligne = curseur.fetchone()
        assert ligne is not None
        produit_id = ligne[0]
        curseur.execute(
            "INSERT INTO transcripts(id, produit_id, contenu, date_entretien, type_source, contexte, locuteurs, nom_fichier, confirme) VALUES (73, %s, 'Texte pseudonymise', '2025-02-03', 'bizdev', 'Contexte', '[{\"identifiant\":\"SPEAKER_01\"}]', 'reunion.pdf', TRUE)",
            (produit_id,),
        )
    assert execute_migrations(base_temporaire, migrations) == [
        "002_pseudonymisation_seule.sql"
    ]
    assert _verifier(
        base_temporaire,
        "SELECT id, produit_id, contenu, date_entretien, type_source, contexte, locuteurs, nom_fichier, confirme FROM transcripts",
    ) == [
        (
            73,
            3,
            "Texte pseudonymise",
            __import__("datetime").date(2025, 2, 3),
            "bizdev",
            "Contexte",
            [{"identifiant": "SPEAKER_01"}],
            "reunion.pdf",
            True,
        )
    ]
    assert _verifier(base_temporaire, "SELECT id, nom FROM produits") == [
        (2, "MSC"),
        (3, "MSS"),
    ]


def test_execute_migrations_annule_schema_et_marqueur_en_erreur(
    base_temporaire: BaseDeDonnees, tmp_path: Path
) -> None:
    (tmp_path / "001_ok.sql").write_text(
        "CREATE TABLE temporaire (id INT);", encoding="utf-8"
    )
    (tmp_path / "002_erreur.sql").write_text(
        "CREATE TABLE autre (id INT); SELECT 1 / 0;", encoding="utf-8"
    )
    with pytest.raises(psycopg2.errors.DivisionByZero):
        execute_migrations(base_temporaire, tmp_path)
    assert _verifier(
        base_temporaire,
        "SELECT to_regclass('public.temporaire'), to_regclass('public.autre')",
    ) == [(None, None)]
    assert _verifier(
        base_temporaire, "SELECT to_regclass('public.migrations_executees')"
    ) == [(None,)]
