from fastapi.testclient import TestClient


def test_lister_vide(client: TestClient):
    assert client.get("/api/produits").json() == []


def test_ajouter(client: TestClient):
    reponse = client.post("/api/produits", json={"nom": "MonProduit"})
    assert reponse.status_code == 201
    assert reponse.json() == {"id": 1, "nom": "MonProduit"}


def test_lister_apres_ajout(client: TestClient):
    client.post("/api/produits", json={"nom": "A"})
    client.post("/api/produits", json={"nom": "B"})
    assert len(client.get("/api/produits").json()) == 2
