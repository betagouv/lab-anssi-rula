import base64

from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.authentification import AuthentificationBasicMiddleware


def _application() -> FastAPI:
    app = FastAPI()
    app.add_middleware(
        AuthentificationBasicMiddleware,
        utilisateur="demo",
        mot_de_passe="mot-de-passe",
    )

    @app.get("/api/sante")
    def sante():
        return {"statut": "ok"}

    @app.get("/prive")
    def prive():
        return {"statut": "prive"}

    return app


def _authorization(utilisateur: str, mot_de_passe: str) -> dict[str, str]:
    valeur = base64.b64encode(f"{utilisateur}:{mot_de_passe}".encode("utf-8")).decode(
        "ascii"
    )
    return {"Authorization": f"Basic {valeur}"}


def test_healthcheck_est_public():
    response = TestClient(_application()).get("/api/sante")

    assert response.status_code == 200


def test_route_privee_refuse_sans_authentification():
    response = TestClient(_application()).get("/prive")

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == 'Basic realm="RULA"'


def test_route_privee_accepte_les_bons_identifiants():
    response = TestClient(_application()).get(
        "/prive", headers=_authorization("demo", "mot-de-passe")
    )

    assert response.status_code == 200


def test_route_privee_refuse_de_mauvais_identifiants():
    response = TestClient(_application()).get(
        "/prive", headers=_authorization("demo", "mauvais")
    )

    assert response.status_code == 401


def test_route_privee_refuse_un_schema_inconnu():
    response = TestClient(_application()).get(
        "/prive", headers={"Authorization": "Bearer jeton"}
    )

    assert response.status_code == 401


def test_route_privee_refuse_une_valeur_base64_invalide():
    response = TestClient(_application()).get(
        "/prive", headers={"Authorization": "Basic invalide"}
    )

    assert response.status_code == 401


def test_route_privee_refuse_des_identifiants_sans_separateur():
    valeur = base64.b64encode(b"demo-sans-separateur").decode("ascii")

    response = TestClient(_application()).get(
        "/prive", headers={"Authorization": f"Basic {valeur}"}
    )

    assert response.status_code == 401
