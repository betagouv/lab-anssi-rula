from collections.abc import Iterator
from typing import NamedTuple

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from api.liste_blanche import fabrique_service_liste_blanche, routeur
from infra.memoire.depot_liste_blanche import DepotListeBlancheMemoire
from liste_blanche.service import ServiceListeBlanche

_ORIGINE = {"Origin": "https://testserver"}


class ApiListeBlancheDeTest(NamedTuple):
    client: TestClient
    depot: DepotListeBlancheMemoire


@pytest.fixture
def api_liste_blanche_de_test() -> Iterator[ApiListeBlancheDeTest]:
    application = FastAPI()
    application.include_router(routeur, prefix="/api")
    depot = DepotListeBlancheMemoire()
    application.dependency_overrides[fabrique_service_liste_blanche] = lambda: (
        ServiceListeBlanche(depot)
    )
    with TestClient(application, base_url="https://testserver") as client:
        yield ApiListeBlancheDeTest(client, depot)


def test_crud_partage_normalise_et_protege_les_conflits(
    api_liste_blanche_de_test: ApiListeBlancheDeTest,
) -> None:
    client = api_liste_blanche_de_test.client
    assert client.get("/api/liste-blanche").json() == []
    ajout = client.post(
        "/api/liste-blanche",
        json={"terme": "  Mon\u00a0  Service Se\u0301curise\u0301  "},
        headers=_ORIGINE,
    )
    assert ajout.status_code == 201
    assert ajout.json() == {
        "id": 1,
        "terme": "Mon Service Sécurisé",
        "revision": 1,
    }
    assert (
        client.post(
            "/api/liste-blanche",
            json={"terme": "MON SERVICE SÉCURISÉ"},
            headers=_ORIGINE,
        ).status_code
        == 409
    )
    modification = client.put(
        "/api/liste-blanche/1",
        json={"terme": "Laboratoire local", "revision": 1},
        headers=_ORIGINE,
    )
    assert modification.json()["revision"] == 2
    assert (
        client.put(
            "/api/liste-blanche/1",
            json={"terme": "Ancienne édition", "revision": 1},
            headers=_ORIGINE,
        ).status_code
        == 409
    )
    assert (
        client.delete("/api/liste-blanche/1?revision=1", headers=_ORIGINE).status_code
        == 409
    )
    assert (
        client.delete("/api/liste-blanche/1?revision=2", headers=_ORIGINE).status_code
        == 204
    )
    assert (
        client.put(
            "/api/liste-blanche/1",
            json={"terme": "Introuvable", "revision": 2},
            headers=_ORIGINE,
        ).status_code
        == 404
    )
    assert (
        client.delete("/api/liste-blanche/1?revision=2", headers=_ORIGINE).status_code
        == 404
    )


@pytest.mark.parametrize("terme", ["", "   ", "!?_ .,", "x" * 121])
def test_refuse_termes_vides_punctuation_ou_trop_longs(
    api_liste_blanche_de_test: ApiListeBlancheDeTest, terme: str
) -> None:
    assert (
        api_liste_blanche_de_test.client.post(
            "/api/liste-blanche", json={"terme": terme}, headers=_ORIGINE
        ).status_code
        == 422
    )


def test_mutation_refuse_une_origine_differente(
    api_liste_blanche_de_test: ApiListeBlancheDeTest,
) -> None:
    assert (
        api_liste_blanche_de_test.client.post(
            "/api/liste-blanche",
            json={"terme": "Nouveau"},
            headers={"Origin": "https://ailleurs.test"},
        ).status_code
        == 403
    )
