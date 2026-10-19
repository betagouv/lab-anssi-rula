from concurrent.futures import ThreadPoolExecutor
from collections.abc import Generator
from datetime import date
import os
from pathlib import Path
import sys
import time
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient
import psycopg2
import pytest
from mcp import Client
from mcp.client.stdio import StdioServerParameters

from api.api import routeur
from api.transcripts_pdf import fabrique_service_preparation_pdf
from configuration import charge_configuration
from infra.postgres.depot_rapports_claude import DepotRapportsClaudePostgres
from infra.postgres.depot_transcripts_pdf import DepotTranscriptsPdfPostgres
from rapports_claude.depot import ConflitIdempotence, SourceModifiee
from rapports_claude.service import ServiceRapportsClaude
from serveur_mcp import fabrique_serveur_mcp
from tests.adaptateurs.albert_de_test import AdaptateurAlbertDeTest
from tests.test_transcripts_pdf import _pdf, _reponses_preparation
from transcripts_pdf.service import ServicePreparationTranscript

pytestmark = pytest.mark.skipif(
    os.getenv("RULA_TEST_POSTGRES") != "1", reason="PostgreSQL integration disabled"
)


@pytest.fixture
def transcript_postgres() -> Generator[tuple[int, int, int, int, int], None, None]:
    configuration = charge_configuration().base_de_donnees
    suffixe = uuid4().hex
    with psycopg2.connect(
        host=configuration.hote,
        dbname=configuration.nom,
        user=configuration.utilisateur,
        password=configuration.mot_de_passe,
        port=configuration.port,
    ) as connexion:
        with connexion.cursor() as curseur:
            curseur.execute(
                "INSERT INTO produits (nom) VALUES (%s) RETURNING id", (suffixe,)
            )
            ligne = curseur.fetchone()
            assert ligne is not None
            produit_id = ligne[0]
            curseur.execute(
                "INSERT INTO projets_recherche (produit_id, nom) VALUES (%s, %s) RETURNING id",
                (produit_id, suffixe),
            )
            ligne = curseur.fetchone()
            assert ligne is not None
            projet_id = ligne[0]
            curseur.execute(
                """INSERT INTO transcripts
                       (produit_id, projet_id, type_source, date_entretien, contenu,
                        contexte, locuteurs, confirme)
                   VALUES (%s, %s, 'produit', %s, %s, %s, '[]', TRUE)
                   RETURNING id""",
                (
                    produit_id,
                    projet_id,
                    date.today(),
                    "é" * 30010,
                    "contexte synthétique",
                ),
            )
            ligne = curseur.fetchone()
            assert ligne is not None
            transcript_id = ligne[0]
            curseur.execute(
                """INSERT INTO transcripts
                       (produit_id, type_source, date_entretien, contenu, confirme)
                   VALUES (%s, 'bizdev', %s, %s, TRUE) RETURNING id""",
                (produit_id, date.today(), "retour BizDev synthétique"),
            )
            ligne = curseur.fetchone()
            assert ligne is not None
            bizdev_id = ligne[0]
            curseur.execute(
                """INSERT INTO transcripts
                       (produit_id, projet_id, type_source, date_entretien, contenu,
                        confirme)
                   VALUES (%s, %s, 'produit', %s, %s, FALSE) RETURNING id""",
                (produit_id, projet_id, date.today(), "source non confirmée"),
            )
            curseur.execute(
                """INSERT INTO transcripts (type_source, date_entretien, contenu)
                   VALUES ('ux', %s, %s) RETURNING id""",
                (date.today(), "source UX"),
            )
            ligne = curseur.fetchone()
            assert ligne is not None
            ux_id = ligne[0]
    yield transcript_id, produit_id, projet_id, bizdev_id, ux_id
    with psycopg2.connect(
        host=configuration.hote,
        dbname=configuration.nom,
        user=configuration.utilisateur,
        password=configuration.mot_de_passe,
        port=configuration.port,
    ) as connexion:
        with connexion.cursor() as curseur:
            curseur.execute("DELETE FROM transcripts WHERE id = %s", (ux_id,))
            curseur.execute("DELETE FROM produits WHERE id = %s", (produit_id,))


def service_postgres() -> ServiceRapportsClaude:
    return ServiceRapportsClaude(
        DepotRapportsClaudePostgres(charge_configuration().base_de_donnees)
    )


def test_postgres_ecriture_idempotence_obsolescence_et_cascade(
    transcript_postgres: tuple[int, int, int, int, int],
) -> None:
    transcript_id, produit_id, _, bizdev_id, _ = transcript_postgres
    service = service_postgres()
    premiere_page = service.lister_transcripts(produit_id=produit_id, limite=1)
    seconde_page = service.lister_transcripts(
        produit_id=produit_id, limite=1, curseur=premiere_page[1]
    )
    assert [item.id for item in premiere_page[0]] == [transcript_id]
    assert premiere_page[1] == transcript_id
    assert [item.id for item in seconde_page[0]] == [bizdev_id]
    assert seconde_page[1] is None
    source = service.lire_source(transcript_id)
    fragments: list[str] = []
    offset = 0
    while True:
        bloc = service.lire_source(
            transcript_id,
            offset,
            source["revision"],
            source["empreinte"],
        )
        fragments.append(bloc["bloc"])
        offset_suivant = bloc["offset_suivant"]
        if offset_suivant is None:
            break
        offset = offset_suivant
    assert len("".join(fragments)) == source["longueur_totale"]
    cle = uuid4()
    premier = service_postgres().enregistrer_analyse(
        transcript_id,
        source["revision"],
        source["empreinte"],
        cle,
        "Analyse synthétique",
    )
    rejoue = service_postgres().enregistrer_analyse(
        transcript_id,
        source["revision"],
        source["empreinte"],
        cle,
        "Analyse synthétique",
    )
    assert rejoue.id == premier.id
    with pytest.raises(ConflitIdempotence):
        service_postgres().enregistrer_analyse(
            transcript_id,
            source["revision"],
            source["empreinte"],
            cle,
            "Une autre analyse",
        )
    DepotTranscriptsPdfPostgres(charge_configuration().base_de_donnees).modifier(
        transcript_id, date.today(), "nouveau texte", "contexte modifié", []
    )
    rejoue_apres_modification = service_postgres().enregistrer_analyse(
        transcript_id,
        source["revision"],
        source["empreinte"],
        cle,
        "Analyse synthétique",
    )
    assert rejoue_apres_modification.id == premier.id
    assert service_postgres().lire_rapport(premier.id)["courant"] is False
    assert (
        service_postgres().lister_transcripts(produit_id=produit_id, statut="analyses")[
            0
        ]
        == []
    )
    assert [
        element.id
        for element in service_postgres().lister_transcripts(
            produit_id=produit_id, statut="non_analyses"
        )[0]
    ] == [transcript_id, bizdev_id]
    with pytest.raises(SourceModifiee):
        service_postgres().lire_source(
            transcript_id, offset, source["revision"], source["empreinte"]
        )
    DepotTranscriptsPdfPostgres(charge_configuration().base_de_donnees).supprimer(
        transcript_id
    )
    with psycopg2.connect(
        host=charge_configuration().base_de_donnees.hote,
        dbname=charge_configuration().base_de_donnees.nom,
        user=charge_configuration().base_de_donnees.utilisateur,
        password=charge_configuration().base_de_donnees.mot_de_passe,
        port=charge_configuration().base_de_donnees.port,
    ) as connexion:
        with connexion.cursor() as curseur:
            curseur.execute(
                "SELECT COUNT(*) FROM rapports_claude WHERE transcript_id = %s",
                (transcript_id,),
            )
            ligne = curseur.fetchone()
            assert ligne is not None and ligne[0] == 0


def test_postgres_rejeu_concurrent_meme_uuid_retourne_le_meme_rapport(
    transcript_postgres: tuple[int, int, int, int, int],
) -> None:
    transcript_id, _, _, _, _ = transcript_postgres
    source = service_postgres().lire_source(transcript_id)
    cle = uuid4()

    def enregistrer() -> int:
        return (
            service_postgres()
            .enregistrer_analyse(
                transcript_id,
                source["revision"],
                source["empreinte"],
                cle,
                "Analyse concurrente synthétique",
            )
            .id
        )

    with ThreadPoolExecutor(max_workers=2) as executeur:
        resultats = list(executeur.map(lambda _: enregistrer(), range(2)))
    assert resultats[0] == resultats[1]


@pytest.mark.asyncio
async def test_serveur_stdio_persiste_un_rapport_entre_processus(
    transcript_postgres: tuple[int, int, int, int, int],
) -> None:
    transcript_id, produit_id, _, _, _ = transcript_postgres
    configuration = charge_configuration().base_de_donnees
    environnement = os.environ | {
        "PYTHONPATH": str(Path(__file__).resolve().parents[2] / "src"),
        "DB_HOTE": configuration.hote,
        "DB_PORT": str(configuration.port),
        "DB_NOM": configuration.nom,
        "DB_UTILISATEUR": configuration.utilisateur,
        "DB_MOT_DE_PASSE": configuration.mot_de_passe,
    }
    parametres = StdioServerParameters(
        command=sys.executable,
        args=["-m", "serveur_mcp"],
        cwd=str(Path(__file__).resolve().parents[2]),
        env=environnement,
    )
    cle = str(uuid4())

    async with Client(parametres) as client:
        catalogue = await client.call_tool(
            "lister_transcripts", {"produit_id": produit_id}
        )
        assert any(
            element["id"] == transcript_id
            for element in catalogue.structured_content["elements"]
        )
        source = await client.call_tool(
            "lire_transcript", {"mode": "source", "transcript_id": transcript_id}
        )
        resultat = await client.call_tool(
            "enregistrer_analyse",
            {
                "transcript_id": transcript_id,
                "revision": source.structured_content["revision"],
                "empreinte": source.structured_content["empreinte"],
                "cle_idempotence": cle,
                "contenu": "Analyse MCP stdio synthétique",
            },
        )
        rapport_id = resultat.structured_content["rapport_id"]

    async with Client(parametres) as client:
        rapport = await client.call_tool(
            "lire_transcript", {"mode": "rapport", "rapport_id": rapport_id}
        )
        assert rapport.structured_content["bloc"] == "Analyse MCP stdio synthétique"


@pytest.mark.asyncio
async def test_preparation_confirmee_mcp_et_lecture_rest(
    transcript_postgres: tuple[int, int, int, int, int],
) -> None:
    _, produit_id, _, _, _ = transcript_postgres
    texte = "Speaker_01: Alice présente une idée."
    service_preparation = ServicePreparationTranscript(
        AdaptateurAlbertDeTest().avec_reponses(
            _reponses_preparation(
                texte, detections=[("transcript", "Alice", "identite")]
            )
        ),
        "Prompt synthétique",
    )
    application = FastAPI()
    application.include_router(routeur, prefix="/api")
    application.dependency_overrides[fabrique_service_preparation_pdf] = lambda: (
        service_preparation
    )
    with TestClient(
        application,
        base_url="https://testserver",
        headers={"Origin": "https://testserver"},
    ) as client:
        avant = client.get(
            "/api/rapports-claude/transcripts",
            params={"produit_id": produit_id, "type_source": "bizdev"},
        ).json()["elements"]
        soumission = client.post(
            "/api/transcripts-pdf/preparation",
            data={"type_source": "bizdev"},
            files={"fichier": ("reunion.pdf", _pdf(texte), "application/pdf")},
        )
        assert soumission.status_code == 202
        jeton = soumission.json()["identifiant"]
        chemin = f"/api/transcripts-pdf/preparation/{jeton}"
        preparation = client.get(chemin).json()
        for _ in range(100):
            if preparation["statut"] != "en_cours":
                break
            time.sleep(0.01)
            preparation = client.get(chemin).json()
        assert preparation["statut"] == "termine"
        assert "Alice" not in preparation["contenu"]
        assert "[IDENTITE_01]" in preparation["contenu"]
        assert (
            client.get(
                "/api/rapports-claude/transcripts",
                params={"produit_id": produit_id, "type_source": "bizdev"},
            ).json()["elements"]
            == avant
        )

        confirmation = client.post(
            "/api/transcripts-pdf",
            json={
                "type_source": "bizdev",
                "nom_source": preparation["nom_source"],
                "produit_id": produit_id,
                "projet_id": None,
                "date_entretien": "2026-10-19",
                "contenu": preparation["contenu"],
                "contexte": preparation["contexte"],
                "locuteurs": preparation["locuteurs"],
            },
        )
        assert confirmation.status_code == 201
        transcript_id = confirmation.json()["id"]
        assert transcript_id not in {element["id"] for element in avant}
        client.delete(chemin)

        depot = DepotRapportsClaudePostgres(charge_configuration().base_de_donnees)
        service = ServiceRapportsClaude(depot)
        async with Client(fabrique_serveur_mcp(lambda: service)) as mcp:
            catalogue = await mcp.call_tool(
                "lister_transcripts",
                {"produit_id": produit_id, "type_source": "bizdev"},
            )
            assert transcript_id in {
                element["id"] for element in catalogue.structured_content["elements"]
            }
            source = await mcp.call_tool(
                "lire_transcript",
                {"mode": "source", "transcript_id": transcript_id},
            )
            assert "[IDENTITE_01]" in source.structured_content["bloc"]
            assert "Alice" not in source.structured_content["bloc"]
            analyse = await mcp.call_tool(
                "enregistrer_analyse",
                {
                    "transcript_id": transcript_id,
                    "revision": source.structured_content["revision"],
                    "empreinte": source.structured_content["empreinte"],
                    "cle_idempotence": str(uuid4()),
                    "contenu": "# Analyse synthétique\n\nBesoin confirmé.",
                },
            )
            rapport_id = analyse.structured_content["rapport_id"]
        historique = client.get(
            f"/api/rapports-claude/transcripts/{transcript_id}/rapports"
        ).json()
        rapport = client.get(f"/api/rapports-claude/{rapport_id}").json()
        assert historique["elements"][0]["id"] == rapport_id
        assert rapport["bloc"] == "# Analyse synthétique\n\nBesoin confirmé."
        assert rapport["courant"]
