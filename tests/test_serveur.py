from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from fastapi.exceptions import RequestValidationError
from typing import cast

from api.erreurs import detail_erreur_validation
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


def test_detail_erreur_validation_gere_un_emplacement_inconnu() -> None:
    assert detail_erreur_validation(
        [{"loc": [], "type": "inconnu"}, {"loc": ["body", "autre"], "type": "inconnu"}]
    ) == {
        "message": "Vérifiez les champs obligatoires avant de continuer.",
        "champs": ["Le champ saisi est invalide.", "Le champ autre est invalide."],
    }


def test_gestion_erreur_validation_retourne_un_detail_structuré() -> None:
    from serveur import gestion_erreur_validation

    response = gestion_erreur_validation(
        cast(Request, None),
        RequestValidationError([{"loc": ("body", "nom"), "type": "missing"}]),
    )

    assert response.status_code == 422
