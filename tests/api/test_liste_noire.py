from collections.abc import Iterator
from typing import NamedTuple

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from api.liste_noire import fabrique_service_liste_noire, routeur
from infra.memoire.depot_liste_noire import DepotListeNoireMemoire
from liste_noire.service import ServiceListeNoire

_ORIGINE = {"Origin": "https://testserver"}


class ApiListeNoireDeTest(NamedTuple):
    client: TestClient
    depot: DepotListeNoireMemoire


@pytest.fixture
def api_liste_noire_de_test() -> Iterator[ApiListeNoireDeTest]:
    application = FastAPI()
    application.include_router(routeur, prefix="/api")
    depot = DepotListeNoireMemoire()
    application.dependency_overrides[fabrique_service_liste_noire] = lambda: (
        ServiceListeNoire(depot)
    )
    with TestClient(application, base_url="https://testserver") as client:
        yield ApiListeNoireDeTest(client, depot)


def test_crud_normalise_et_protege_les_conflits(
    api_liste_noire_de_test: ApiListeNoireDeTest,
) -> None:
    client = api_liste_noire_de_test.client
    assert client.get("/api/liste-noire").json() == []
    ajout = client.post(
        "/api/liste-noire",
        json={"terme": "  Jean\u00a0  Dupont  "},
        headers=_ORIGINE,
    )
    assert ajout.status_code == 201
    assert ajout.json() == {"id": 1, "terme": "Jean Dupont", "revision": 1}
    assert (
        client.post(
            "/api/liste-noire", json={"terme": "JEAN   DUPONT"}, headers=_ORIGINE
        ).status_code
        == 409
    )
    assert (
        client.put(
            "/api/liste-noire/1",
            json={"terme": "Autre terme", "revision": 1},
            headers=_ORIGINE,
        ).json()["revision"]
        == 2
    )
    assert (
        client.delete("/api/liste-noire/1?revision=2", headers=_ORIGINE).status_code
        == 204
    )
    assert (
        client.put(
            "/api/liste-noire/1",
            json={"terme": "Absent", "revision": 2},
            headers=_ORIGINE,
        ).status_code
        == 404
    )


@pytest.mark.parametrize("terme", ["", "   ", "!?_ .", "x" * 121])
def test_refuse_termes_invalides(
    api_liste_noire_de_test: ApiListeNoireDeTest, terme: str
) -> None:
    assert (
        api_liste_noire_de_test.client.post(
            "/api/liste-noire", json={"terme": terme}, headers=_ORIGINE
        ).status_code
        == 422
    )


def test_mutation_refuse_une_origine_differente(
    api_liste_noire_de_test: ApiListeNoireDeTest,
) -> None:
    assert (
        api_liste_noire_de_test.client.post(
            "/api/liste-noire",
            json={"terme": "Confidentiel"},
            headers={"Origin": "https://ailleurs.test"},
        ).status_code
        == 403
    )
