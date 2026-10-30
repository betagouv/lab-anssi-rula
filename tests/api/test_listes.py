from collections.abc import Iterator
from typing import NamedTuple

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from api.liste_blanche import fabrique_service_liste_blanche, routeur as routeur_blanche
from api.liste_noire import fabrique_service_liste_noire, routeur as routeur_noire
from infra.memoire.depot_termes import DepotListeTermesMemoire
from termes_liste import CouleurListe, ServiceListeTermes

_ORIGINE = {"Origin": "https://testserver"}


class ApiListeDeTest(NamedTuple):
    client: TestClient
    depot: DepotListeTermesMemoire
    couleur: CouleurListe


@pytest.fixture(
    params=[
        ("blanche", routeur_blanche, fabrique_service_liste_blanche),
        ("noire", routeur_noire, fabrique_service_liste_noire),
    ]
)
def api_liste_de_test(request: pytest.FixtureRequest) -> Iterator[ApiListeDeTest]:
    couleur, routeur, fabrique = request.param
    application = FastAPI()
    application.include_router(routeur, prefix="/api")
    depot = DepotListeTermesMemoire()
    application.dependency_overrides[fabrique] = lambda: ServiceListeTermes(depot)
    with TestClient(application, base_url="https://testserver") as client:
        yield ApiListeDeTest(client, depot, couleur)


def test_crud_normalise_et_protege_les_conflits(
    api_liste_de_test: ApiListeDeTest,
) -> None:
    client = api_liste_de_test.client
    chemin = f"/api/liste-{api_liste_de_test.couleur}"
    assert client.get(chemin).json() == []
    ajout = client.post(
        chemin,
        json={"terme": "  Mon\u00a0  Service Se\u0301curise\u0301  "},
        headers=_ORIGINE,
    )
    assert ajout.status_code == 201
    assert ajout.json() == {"id": 1, "terme": "Mon Service Sécurisé", "revision": 1}
    assert (
        client.post(
            chemin, json={"terme": "MON SERVICE SÉCURISÉ"}, headers=_ORIGINE
        ).status_code
        == 409
    )
    assert (
        client.put(
            f"{chemin}/1",
            json={"terme": "Laboratoire local", "revision": 1},
            headers=_ORIGINE,
        ).json()["revision"]
        == 2
    )
    assert (
        client.put(
            f"{chemin}/1",
            json={"terme": "Ancienne édition", "revision": 1},
            headers=_ORIGINE,
        ).status_code
        == 409
    )
    assert client.delete(f"{chemin}/1?revision=1", headers=_ORIGINE).status_code == 409
    assert client.delete(f"{chemin}/1?revision=2", headers=_ORIGINE).status_code == 204
    assert (
        client.put(
            f"{chemin}/1",
            json={"terme": "Introuvable", "revision": 2},
            headers=_ORIGINE,
        ).status_code
        == 404
    )
    assert client.delete(f"{chemin}/1?revision=2", headers=_ORIGINE).status_code == 404


@pytest.mark.parametrize("terme", ["", "   ", "!?_ .", "x" * 121])
def test_refuse_termes_invalides(api_liste_de_test: ApiListeDeTest, terme: str) -> None:
    chemin = f"/api/liste-{api_liste_de_test.couleur}"
    assert (
        api_liste_de_test.client.post(
            chemin, json={"terme": terme}, headers=_ORIGINE
        ).status_code
        == 422
    )


def test_mutation_refuse_une_origine_differente(
    api_liste_de_test: ApiListeDeTest,
) -> None:
    chemin = f"/api/liste-{api_liste_de_test.couleur}"
    assert (
        api_liste_de_test.client.post(
            chemin,
            json={"terme": "Nouveau"},
            headers={"Origin": "https://ailleurs.test"},
        ).status_code
        == 403
    )


def test_listes_sont_independantes() -> None:
    application = FastAPI()
    application.include_router(routeur_blanche, prefix="/api")
    application.include_router(routeur_noire, prefix="/api")
    blanche = DepotListeTermesMemoire()
    noire = DepotListeTermesMemoire()
    application.dependency_overrides[fabrique_service_liste_blanche] = lambda: (
        ServiceListeTermes(blanche)
    )
    application.dependency_overrides[fabrique_service_liste_noire] = lambda: (
        ServiceListeTermes(noire)
    )
    with TestClient(application, base_url="https://testserver") as client:
        assert (
            client.post(
                "/api/liste-blanche", json={"terme": "Même terme"}, headers=_ORIGINE
            ).status_code
            == 201
        )
        assert client.get("/api/liste-noire").json() == []
        assert (
            client.post(
                "/api/liste-noire", json={"terme": "Même terme"}, headers=_ORIGINE
            ).status_code
            == 201
        )
        assert client.get("/api/liste-blanche").json() == [
            {"id": 1, "terme": "Même terme", "revision": 1}
        ]
