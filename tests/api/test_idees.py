import pytest
from fastapi.testclient import TestClient

from adaptateurs.featurebase import AdaptateurFeatureBase, IdeeBrute
from api.idees import fabrique_service_idees
from idees.service import ServiceIdees
from infra.memoire.depot_idees import DepotIdeesMemoire
from serveur import app


class _FeatureBaseErreurValeurDeTest(AdaptateurFeatureBase):
    def lister_idees(self) -> list[IdeeBrute]:
        raise ValueError("FEATUREBASE_CLE_API non configurée")


class _FeatureBaseErreurHttpDeTest(AdaptateurFeatureBase):
    def lister_idees(self) -> list[IdeeBrute]:
        import httpx

        response = httpx.Response(403, request=httpx.Request("GET", "https://example.com"))
        raise httpx.HTTPStatusError("403", request=response.request, response=response)


def _client_avec(client: TestClient, featurebase: AdaptateurFeatureBase) -> TestClient:
    service = ServiceIdees(depot=DepotIdeesMemoire(), featurebase=featurebase)
    app.dependency_overrides[fabrique_service_idees] = lambda: service
    return client


def test_sync_retourne_503_si_cle_manquante(client: TestClient) -> None:
    r = _client_avec(client, _FeatureBaseErreurValeurDeTest()).post("/api/idees/sync")
    assert r.status_code == 503
    assert "FEATUREBASE_CLE_API" in r.json()["detail"]


def test_sync_retourne_503_si_api_inaccessible(client: TestClient) -> None:
    r = _client_avec(client, _FeatureBaseErreurHttpDeTest()).post("/api/idees/sync")
    assert r.status_code == 503
    assert "403" in r.json()["detail"]


def test_lister_vide(client: TestClient) -> None:
    r = client.get("/api/idees")
    assert r.status_code == 200
    assert r.json() == []


def test_sync_retourne_les_idees(client: TestClient) -> None:
    r = client.post("/api/idees/sync")
    assert r.status_code == 200
    assert len(r.json()) == 2
    assert r.json()[0]["titre"] == "Idée A"
    assert r.json()[0]["nb_votes"] == 10
    assert r.json()[1]["titre"] == "Idée B"
    assert r.json()[1]["nb_votes"] == 5


def test_sync_idempotent(client: TestClient) -> None:
    client.post("/api/idees/sync")
    r = client.post("/api/idees/sync")
    assert r.status_code == 200
    assert len(r.json()) == 2


def test_lister_apres_sync(client: TestClient) -> None:
    client.post("/api/idees/sync")
    r = client.get("/api/idees")
    assert r.status_code == 200
    assert len(r.json()) == 2
    assert r.json()[0]["nb_votes"] >= r.json()[1]["nb_votes"]
