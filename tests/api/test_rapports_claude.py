from datetime import datetime, timezone
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.rapports_claude import fabrique_service_rapports_claude, routeur
from infra.memoire.depot_rapports_claude import DepotRapportsClaudeDeTest
from rapports_claude.depot import SourceTranscriptClaude
from rapports_claude.service import ServiceRapportsClaude


def client_rapports() -> tuple[
    TestClient, ServiceRapportsClaude, DepotRapportsClaudeDeTest
]:
    depot = DepotRapportsClaudeDeTest()
    source = SourceTranscriptClaude(
        1,
        "produit",
        2,
        3,
        1,
        True,
        "contenu synthétique",
        "contexte synthétique",
        [],
        datetime.now(timezone.utc),
    )
    depot.ajouter_source(source)
    service = ServiceRapportsClaude(depot)
    app = FastAPI()
    app.include_router(routeur, prefix="/api")
    app.dependency_overrides[fabrique_service_rapports_claude] = lambda: service
    return TestClient(app), service, depot


def test_routes_de_lecture_catalogue_source_et_historique() -> None:
    client, service, _ = client_rapports()
    source = service.lire_source(1)
    rapport = service.enregistrer_analyse(
        1,
        source["revision"],
        source["empreinte"],
        uuid4(),
        "# Analyse synthétique",
    )
    catalogue = client.get("/api/rapports-claude/transcripts")
    lecture = client.get("/api/rapports-claude/transcripts/1")
    historique = client.get("/api/rapports-claude/transcripts/1/rapports")
    detail = client.get(f"/api/rapports-claude/{rapport.id}")
    assert catalogue.status_code == lecture.status_code == 200
    assert catalogue.json()["elements"][0]["id"] == 1
    assert "contenu" not in catalogue.json()["elements"][0]
    assert lecture.json()["empreinte"] == source["empreinte"]
    assert historique.json()["elements"][0]["courant"] is True
    assert detail.json()["bloc"] == "# Analyse synthétique"
    assert client.post("/api/rapports-claude/transcripts/1/rapports").status_code == 405


def test_routes_rejettent_les_lectures_obsoletes_et_les_sources_inconnues() -> None:
    client, service, depot = client_rapports()
    source = service.lire_source(1)
    depot.ajouter_source(
        SourceTranscriptClaude(
            1,
            "produit",
            2,
            3,
            2,
            True,
            "contenu modifié",
            "contexte synthétique",
            [],
            datetime.now(timezone.utc),
        )
    )
    modifie = client.get(
        "/api/rapports-claude/transcripts/1",
        params={
            "offset": 2,
            "revision": source["revision"],
            "empreinte": source["empreinte"],
        },
    )
    absent = client.get("/api/rapports-claude/transcripts/9")
    assert modifie.status_code == 409
    assert absent.status_code == 404
