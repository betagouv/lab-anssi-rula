from fastapi import FastAPI
from fastapi.testclient import TestClient

from configuration import Authentification
from serveur import ajoute_authentification, ajoute_frontend


def test_ajoute_frontend_retourne_faux_sans_build(tmp_path):
    assert ajoute_frontend(FastAPI(), tmp_path) is False


def test_ajoute_frontend_sert_le_build(tmp_path):
    (tmp_path / "index.html").write_text("<h1>RULA</h1>", encoding="utf-8")
    app = FastAPI()

    assert ajoute_frontend(app, tmp_path) is True
    response = TestClient(app).get("/")

    assert response.status_code == 200
    assert response.text == "<h1>RULA</h1>"


def test_ajoute_authentification_protege_l_application():
    app = FastAPI()
    ajoute_authentification(app, Authentification("demo", "mot-de-passe"))

    @app.get("/prive")
    def prive():
        return {"statut": "prive"}

    response = TestClient(app).get("/prive")

    assert response.status_code == 401
