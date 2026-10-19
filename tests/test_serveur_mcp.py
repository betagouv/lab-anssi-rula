from datetime import datetime, timezone
from uuid import uuid4

import httpx2
import pytest
from mcp import Client
from mcp.client.streamable_http import streamable_http_client
from pydantic import SecretStr
from starlette.testclient import TestClient

from configuration import charge_configuration
from infra.memoire.depot_rapports_claude import DepotRapportsClaudeDeTest
from rapports_claude.depot import SourceTranscriptClaude
from rapports_claude.service import ServiceRapportsClaude
from serveur_mcp import cree_application_http, fabrique_serveur_mcp


def service_test() -> tuple[ServiceRapportsClaude, DepotRapportsClaudeDeTest]:
    depot = DepotRapportsClaudeDeTest()
    depot.ajouter_source(
        SourceTranscriptClaude(
            1,
            "produit",
            7,
            None,
            1,
            True,
            "Transcript anonymisé",
            "Contexte synthétique",
            [],
            datetime.now(timezone.utc),
        )
    )
    return ServiceRapportsClaude(depot), depot


def configuration_test(jeton: str):
    configuration = charge_configuration()
    return configuration._replace(
        mcp=configuration.mcp._replace(hote="localhost", jeton=SecretStr(jeton))
    )


@pytest.mark.asyncio
async def test_client_mcp_liste_lit_enregistre_et_refuse_le_rejeu_different() -> None:
    service, _ = service_test()
    serveur = fabrique_serveur_mcp(lambda: service)

    async with Client(serveur) as client:
        outils = await client.list_tools()
        assert {outil.name for outil in outils.tools} == {
            "lister_transcripts",
            "lire_transcript",
            "enregistrer_analyse",
        }

        catalogue = await client.call_tool("lister_transcripts", {})
        source = await client.call_tool(
            "lire_transcript", {"mode": "source", "transcript_id": 1}
        )
        assert catalogue.structured_content["elements"][0]["id"] == 1
        assert source.structured_content["bloc"].endswith("Transcript anonymisé")

        arguments = {
            "transcript_id": 1,
            "revision": source.structured_content["revision"],
            "empreinte": source.structured_content["empreinte"],
            "cle_idempotence": str(uuid4()),
            "contenu": "# Analyse synthétique",
        }
        resultat = await client.call_tool("enregistrer_analyse", arguments)
        assert not resultat.is_error

        historique = await client.call_tool(
            "lire_transcript", {"mode": "historique", "transcript_id": 1}
        )
        rapport_id = historique.structured_content["elements"][0]["id"]
        rapport = await client.call_tool(
            "lire_transcript", {"mode": "rapport", "rapport_id": rapport_id}
        )
        assert rapport.structured_content["bloc"] == "# Analyse synthétique"

        conflit = await client.call_tool(
            "enregistrer_analyse", {**arguments, "contenu": "Autre contenu"}
        )
        assert conflit.is_error


def test_http_exige_un_jeton_et_ne_protege_pas_la_sante() -> None:
    service, _ = service_test()
    application = cree_application_http(
        fabrique_serveur_mcp(lambda: service),
        configuration_test("jeton-test"),
        verification_schema=lambda: None,
    )

    with TestClient(application) as client:
        assert client.get("/healthz").status_code == 200
        assert client.post("/mcp").status_code == 401
        assert (
            client.post("/mcp", headers={"Authorization": "Bearer faux"}).status_code
            == 401
        )
        assert (
            client.post(
                "/mcp", headers=[(b"Authorization", b"Bearer \xff")]
            ).status_code
            == 401
        )
        assert client.get("/autre").status_code == 401


def test_http_refuse_de_demarrer_sans_jeton() -> None:
    service, _ = service_test()
    application = cree_application_http(
        fabrique_serveur_mcp(lambda: service),
        configuration_test(""),
        verification_schema=lambda: None,
    )
    with pytest.raises(RuntimeError, match="RULA_MCP_BEARER_TOKEN est obligatoire"):
        with TestClient(application):
            pass


@pytest.mark.asyncio
async def test_client_mcp_http_accepte_le_bearer_et_refuse_le_faux() -> None:
    service, _ = service_test()
    application = cree_application_http(
        fabrique_serveur_mcp(lambda: service),
        configuration_test("jeton-test"),
        verification_schema=lambda: None,
    )

    async with application.router.lifespan_context(application):
        async with httpx2.AsyncClient(
            transport=httpx2.ASGITransport(app=application),
            base_url="http://localhost:8000",
            headers={"Authorization": "Bearer jeton-test"},
        ) as client_http:
            async with Client(
                streamable_http_client(
                    "http://localhost:8000/mcp", http_client=client_http
                )
            ) as client_mcp:
                resultat = await client_mcp.call_tool("lister_transcripts", {})
                assert resultat.structured_content["elements"][0]["id"] == 1
