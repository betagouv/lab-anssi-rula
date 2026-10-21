from datetime import date
from pathlib import Path
from uuid import uuid4
import os

import psycopg2
from psycopg2 import sql
import pytest

from configuration import BaseDeDonnees
from infra.postgres.depot_liste_blanche import DepotListeBlanchePostgres
from infra.postgres.migrations import execute_migrations
from liste_blanche.depot import RevisionObsolete, TermeDejaPresent
from liste_blanche.service import ServiceListeBlanche


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
        "003_liste_blanche.sql",
    ]
    assert execute_migrations(base_temporaire, repertoire) == []
    assert _verifier(base_temporaire, "SELECT nom FROM produits ORDER BY nom") == [
        ("MSC",),
        ("MSS",),
    ]
    assert _verifier(base_temporaire, "SELECT count(*) FROM transcripts")[0][0] == 0
    assert _verifier(
        base_temporaire,
        "SELECT terme FROM termes_liste_blanche ORDER BY terme_normalise",
    ) == [
        ("Annecy",),
        ("ANSI",),
        ("LAB",),
        ("Laboratoire d’innovation de l’ANSSI",),
        ("Mon Service Sécurisé",),
        ("MSS",),
    ]
    assert _verifier(
        base_temporaire,
        "DELETE FROM termes_liste_blanche WHERE terme = 'MSS' RETURNING terme",
    ) == [("MSS",)]
    assert execute_migrations(base_temporaire, repertoire) == []
    assert _verifier(
        base_temporaire,
        "SELECT count(*) FROM termes_liste_blanche WHERE terme = 'MSS'",
    ) == [(0,)]


def test_migration_ne_garde_que_les_transcripts_pdf_confirmes_mss_msc(
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
        curseur.execute("SELECT nom, id FROM produits")
        produits = dict(curseur.fetchall())
        curseur.executemany(
            "INSERT INTO projets_recherche(id, produit_id, nom) VALUES (%s, %s, %s)",
            [
                (901, produits["MSS"], "Projet MSS"),
                (902, produits["MSC"], "Projet MSC"),
                (903, produits["MQC"], "Projet hors périmètre"),
            ],
        )
        curseur.execute(
            """
            INSERT INTO transcripts(
                id, produit_id, projet_id, contenu, date_entretien, type_source,
                contexte, locuteurs, nom_fichier, confirme
            ) VALUES
                (71, %s, 901, 'MSS produit confirmé', '2025-02-01', 'produit',
                 'Contexte 71', '[{"identifiant":"SPEAKER_01"}]', '71.pdf', TRUE),
                (72, %s, NULL, 'MSS bizdev confirmé', '2025-02-02', 'bizdev',
                 'Contexte 72', '[{"identifiant":"SPEAKER_02"}]', '72.pdf', TRUE),
                (73, %s, 902, 'MSC produit confirmé', '2025-02-03', 'produit',
                 'Contexte 73', '[{"identifiant":"SPEAKER_03"}]', '73.pdf', TRUE),
                (74, %s, NULL, 'MSC bizdev confirmé', '2025-02-04', 'bizdev',
                 'Contexte 74', '[{"identifiant":"SPEAKER_04"}]', '74.pdf', TRUE),
                (75, %s, 901, 'MSS produit non confirmé', '2025-02-05', 'produit',
                 '', '[]', '75.pdf', FALSE),
                (76, %s, NULL, 'MSC bizdev non confirmé', '2025-02-06', 'bizdev',
                 '', '[]', '76.pdf', FALSE),
                (77, %s, NULL, 'MSS UX confirmé', '2025-02-07', 'ux',
                 '', '[]', '77.pdf', TRUE),
                (78, %s, 903, 'MQC produit confirmé', '2025-02-08', 'produit',
                 '', '[]', '78.pdf', TRUE),
                (79, %s, NULL, 'MQC bizdev confirmé', '2025-02-09', 'bizdev',
                 '', '[]', '79.pdf', TRUE),
                (80, NULL, NULL, 'Sans produit confirmé', '2025-02-10', 'ux',
                 '', '[]', '80.pdf', TRUE)
            """,
            (
                produits["MSS"],
                produits["MSS"],
                produits["MSC"],
                produits["MSC"],
                produits["MSS"],
                produits["MSC"],
                produits["MSS"],
                produits["MQC"],
                produits["MQC"],
            ),
        )
    assert execute_migrations(base_temporaire, migrations) == [
        "002_pseudonymisation_seule.sql",
        "003_liste_blanche.sql",
    ]
    assert _verifier(
        base_temporaire,
        """
        SELECT id, produit_id, contenu, date_entretien, type_source, contexte,
               locuteurs, nom_fichier, confirme
        FROM transcripts ORDER BY id
        """,
    ) == [
        (
            71,
            3,
            "MSS produit confirmé",
            date(2025, 2, 1),
            "produit",
            "Contexte 71",
            [{"identifiant": "SPEAKER_01"}],
            "71.pdf",
            True,
        ),
        (
            72,
            3,
            "MSS bizdev confirmé",
            date(2025, 2, 2),
            "bizdev",
            "Contexte 72",
            [{"identifiant": "SPEAKER_02"}],
            "72.pdf",
            True,
        ),
        (
            73,
            2,
            "MSC produit confirmé",
            date(2025, 2, 3),
            "produit",
            "Contexte 73",
            [{"identifiant": "SPEAKER_03"}],
            "73.pdf",
            True,
        ),
        (
            74,
            2,
            "MSC bizdev confirmé",
            date(2025, 2, 4),
            "bizdev",
            "Contexte 74",
            [{"identifiant": "SPEAKER_04"}],
            "74.pdf",
            True,
        ),
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


def test_depot_postgres_applique_revision_et_unicite_normalisee(
    base_temporaire: BaseDeDonnees,
) -> None:
    execute_migrations(base_temporaire)
    service = ServiceListeBlanche(DepotListeBlanchePostgres(base_temporaire))
    premier = service.ajouter("  Entreprise\u00a0locale ")
    second = service.ajouter("Autre terme")
    with pytest.raises(TermeDejaPresent):
        service.ajouter("ENTREPRISE   LOCALE")
    with pytest.raises(TermeDejaPresent):
        service.modifier(premier.id, "AUTRE TERME", premier.revision)
    modifie = service.modifier(premier.id, "Équipe locale", premier.revision)
    assert modifie.revision == 2
    with pytest.raises(RevisionObsolete):
        service.modifier(premier.id, "Ancien client", premier.revision)
    with pytest.raises(RevisionObsolete):
        service.supprimer(second.id, second.revision + 1)
    service.supprimer(second.id, second.revision)
    assert [terme for terme in service.lister() if terme.id == premier.id] == [
        type(premier)(premier.id, "Équipe locale", 2)
    ]
    assert all(terme.id != second.id for terme in service.lister())
