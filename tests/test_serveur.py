from fastapi import FastAPI
from fastapi.testclient import TestClient

from serveur import ajoute_frontend


def test_ajoute_frontend_retourne_faux_sans_build(tmp_path):
    assert ajoute_frontend(FastAPI(), tmp_path) is False


def test_ajoute_frontend_sert_le_build(tmp_path):
    (tmp_path / "index.html").write_text("<h1>RULA</h1>", encoding="utf-8")
    app = FastAPI()

    assert ajoute_frontend(app, tmp_path) is True
    response = TestClient(app).get("/")

    assert response.status_code == 200
    assert response.text == "<h1>RULA</h1>"
