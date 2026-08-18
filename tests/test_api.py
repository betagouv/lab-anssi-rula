from fastapi.testclient import TestClient

import api.api as api
from serveur import app

client = TestClient(app)


def test_sante(monkeypatch):
    monkeypatch.setattr(api, "base_de_donnees_est_disponible", lambda config: True)
    response = client.get("/api/sante")
    assert response.status_code == 200
    assert response.json() == {"statut": "ok"}


def test_sante_indisponible(monkeypatch):
    monkeypatch.setattr(api, "base_de_donnees_est_disponible", lambda config: False)
    response = client.get("/api/sante")
    assert response.status_code == 503
    assert response.json() == {"detail": "Base de données indisponible"}
