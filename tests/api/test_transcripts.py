from fastapi.testclient import TestClient

from adaptateurs.albert import AdaptateurAlbertReel
from api.transcripts import fabrique_service_validation_transcript
from tests.adaptateurs.albert_de_test import AdaptateurAlbertDeTest

PAYLOAD = {
    "identite_id": 1,
    "produit_id": 1,
    "date_entretien": "2026-06-16",
    "contenu": "L'utilisateur a dit que la navigation est confuse.",
}


def test_fabrique_le_service_de_validation_avec_albert_reel():
    service = fabrique_service_validation_transcript()

    assert isinstance(service._albert, AdaptateurAlbertReel)


def test_lister_vide(client: TestClient):
    assert client.get("/api/transcripts").json() == []


def test_ajouter(client: TestClient):
    reponse = client.post("/api/transcripts", json=PAYLOAD)
    assert reponse.status_code == 201
    data = reponse.json()
    assert data["id"] == 1
    assert data["identite_id"] == 1
    assert data["contenu"] == PAYLOAD["contenu"]


def test_ajouter_avec_une_nouvelle_identite_et_un_nouveau_projet(client: TestClient):
    reponse = client.post(
        "/api/transcripts",
        json={
            "nouvelle_identite": "Une identité",
            "nouveau_produit": "Un projet",
            "date_entretien": "2026-06-16",
            "contenu": "Un besoin produit anonymisé.",
        },
    )

    assert reponse.status_code == 201
    assert client.get("/api/identites").json()[0]["nom"] == "Une identité"
    assert client.get("/api/produits").json()[0]["nom"] == "Un projet"


def test_refuse_un_transcript_non_conforme_sans_creer_les_nouvelles_ressources(
    client: TestClient, albert_validation: AdaptateurAlbertDeTest
):
    albert_validation.avec_reponse(
        '{"valide":false,"problemes":[{"categorie":"identite","element":"Alice Martin","raison":"Nom complet d’une personne."}]}'
    )

    reponse = client.post(
        "/api/transcripts",
        json={
            "nouvelle_identite": "Une identité",
            "nouveau_produit": "Un projet",
            "date_entretien": "2026-06-16",
            "contenu": "Alice Martin a décrit un besoin.",
        },
    )

    assert reponse.status_code == 422
    assert reponse.json()["detail"]["raisons"] == [
        {
            "categorie": "identite",
            "element": "Alice Martin",
            "raison": "Nom complet d’une personne.",
        }
    ]
    assert client.get("/api/transcripts").json() == []
    assert client.get("/api/identites").json() == []
    assert client.get("/api/produits").json() == []


def test_refuse_si_albert_ne_peut_pas_verifier(
    client: TestClient, albert_validation: AdaptateurAlbertDeTest
):
    albert_validation.avec_erreur(RuntimeError("Albert indisponible"))

    reponse = client.post("/api/transcripts", json=PAYLOAD)

    assert reponse.status_code == 503
    assert client.get("/api/transcripts").json() == []


def test_refuse_si_albert_renvoie_un_json_invalide(
    client: TestClient, albert_validation: AdaptateurAlbertDeTest
):
    albert_validation.avec_reponse("pas du JSON")

    reponse = client.post("/api/transcripts", json=PAYLOAD)

    assert reponse.status_code == 503
    assert client.get("/api/transcripts").json() == []


def test_refuse_une_identite_a_la_fois_selectionnee_et_nouvelle(client: TestClient):
    reponse = client.post(
        "/api/transcripts",
        json={
            **PAYLOAD,
            "nouvelle_identite": "Une identité",
        },
    )

    assert reponse.status_code == 422


def test_ne_modifie_pas_un_transcript_non_conforme(
    client: TestClient, albert_validation: AdaptateurAlbertDeTest
):
    client.post("/api/transcripts", json=PAYLOAD)
    albert_validation.avec_reponse(
        '{"valide":false,"problemes":[{"categorie":"technologie_ou_produit","element":"ProduitX","raison":"Nom de produit."}]}'
    )

    reponse = client.put(
        "/api/transcripts/1", json={**PAYLOAD, "contenu": "ProduitX est utilisé."}
    )

    assert reponse.status_code == 422
    assert client.get("/api/transcripts/1").json()["contenu"] == PAYLOAD["contenu"]


def test_lister_apres_ajout(client: TestClient):
    client.post("/api/transcripts", json=PAYLOAD)
    client.post(
        "/api/transcripts",
        json={**PAYLOAD, "identite_id": 2, "contenu": "Transcript B"},
    )
    assert len(client.get("/api/transcripts").json()) == 2


def test_obtenir(client: TestClient):
    client.post("/api/transcripts", json=PAYLOAD)
    reponse = client.get("/api/transcripts/1")
    assert reponse.status_code == 200
    assert reponse.json()["id"] == 1


def test_obtenir_inexistant(client: TestClient):
    assert client.get("/api/transcripts/999").status_code == 404


def test_modifier(client: TestClient):
    client.post("/api/transcripts", json=PAYLOAD)
    reponse = client.put(
        "/api/transcripts/1", json={**PAYLOAD, "contenu": "Nouveau contenu"}
    )
    assert reponse.status_code == 200
    assert reponse.json()["contenu"] == "Nouveau contenu"


def test_modifier_inexistant(client: TestClient):
    assert client.put("/api/transcripts/999", json=PAYLOAD).status_code == 404


def test_supprimer(client: TestClient):
    client.post("/api/transcripts", json=PAYLOAD)
    reponse = client.delete("/api/transcripts/1")
    assert reponse.status_code == 204
    assert client.get("/api/transcripts").json() == []


def test_supprimer_inexistant(client: TestClient):
    assert client.delete("/api/transcripts/999").status_code == 404
