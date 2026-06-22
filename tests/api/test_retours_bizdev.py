from fastapi.testclient import TestClient

CSV_SIMPLE = "Verbatim,User nom,Rôle du user,Type cible,Source,Lien,Date,Qui ?,Catégorie,Item\nElle aimerait une vue d'ensemble,Alice,RSSI,,Itw quali,,18/01/24,Laura,[SUPER ADMIN],Vue d'ensemble\nIl manque une typologie IoT,Bob,RSSI,,Itw quali,,18/01/24,Laura,[DECRIRE],Typologie projet\n"
CSV_VIDE = "Verbatim,User nom,Rôle du user,Type cible,Source,Lien,Date,Qui ?,Catégorie,Item\n"


def test_lister_vide(client: TestClient) -> None:
    r = client.get("/api/retours-bizdev")
    assert r.status_code == 200
    assert r.json() == []


def test_import_retourne_les_retours(client: TestClient) -> None:
    r = client.post("/api/retours-bizdev/import", files={"fichier": ("retours.csv", CSV_SIMPLE.encode(), "text/csv")})
    assert r.status_code == 200
    assert len(r.json()) == 2
    assert r.json()[0]["verbatim"] == "Elle aimerait une vue d'ensemble"
    assert r.json()[0]["categorie"] == "[SUPER ADMIN]"
    assert r.json()[0]["item"] == "Vue d'ensemble"
    assert r.json()[0]["role"] == "RSSI"
    assert r.json()[0]["qui"] == "Laura"
    assert r.json()[0]["date_retour"] == "18/01/24"


def test_import_remplace_les_retours(client: TestClient) -> None:
    client.post("/api/retours-bizdev/import", files={"fichier": ("retours.csv", CSV_SIMPLE.encode(), "text/csv")})
    csv2 = "Verbatim,User nom,Rôle du user,Type cible,Source,Lien,Date,Qui ?,Catégorie,Item\nNouveau retour,,,,,,,,[TEST],Item test\n"
    r = client.post("/api/retours-bizdev/import", files={"fichier": ("retours.csv", csv2.encode(), "text/csv")})
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["verbatim"] == "Nouveau retour"


def test_import_csv_vide(client: TestClient) -> None:
    r = client.post("/api/retours-bizdev/import", files={"fichier": ("retours.csv", CSV_VIDE.encode(), "text/csv")})
    assert r.status_code == 200
    assert r.json() == []


def test_import_csv_invalide_retourne_400(client: TestClient) -> None:
    csv_sans_colonne = "Titre,Nombre\nRetour A,10\n"
    r = client.post("/api/retours-bizdev/import", files={"fichier": ("retours.csv", csv_sans_colonne.encode(), "text/csv")})
    assert r.status_code == 400
    assert "CSV invalide" in r.json()["detail"]


def test_lister_apres_import(client: TestClient) -> None:
    client.post("/api/retours-bizdev/import", files={"fichier": ("retours.csv", CSV_SIMPLE.encode(), "text/csv")})
    r = client.get("/api/retours-bizdev")
    assert r.status_code == 200
    assert len(r.json()) == 2


def test_import_csv_cp1252_avec_bom(client: TestClient) -> None:
    # BOM UTF-8 + contenu cp1252 : cas typique des exports Excel français
    contenu = "Verbatim,User nom,Rôle du user,Type cible,Source,Lien,Date,Qui ?,Catégorie,Item\nRetour encodé,Alice,RSSI,,,,01/01/24,Bob,[CAT],Item\n"
    csv_bom_cp1252 = b"\xef\xbb\xbf" + contenu.encode("cp1252")
    r = client.post("/api/retours-bizdev/import", files={"fichier": ("retours.csv", csv_bom_cp1252, "text/csv")})
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["verbatim"] == "Retour encodé"


def test_import_csv_cp1252_sans_bom(client: TestClient) -> None:
    csv_cp1252 = "Verbatim,User nom,Rôle du user,Type cible,Source,Lien,Date,Qui ?,Catégorie,Item\nRetour encodé,Alice,RSSI,,,,01/01/24,Bob,[CAT],Item\n".encode("cp1252")
    r = client.post("/api/retours-bizdev/import", files={"fichier": ("retours.csv", csv_cp1252, "text/csv")})
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["verbatim"] == "Retour encodé"


def test_ignore_verbatim_vide(client: TestClient) -> None:
    csv_avec_vide = "Verbatim,User nom,Rôle du user,Type cible,Source,Lien,Date,Qui ?,Catégorie,Item\nRetour valide,,,,,,,,[CAT],Item\n   ,,,,,,,,,[CAT2],Item2\n"
    r = client.post("/api/retours-bizdev/import", files={"fichier": ("retours.csv", csv_avec_vide.encode(), "text/csv")})
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["verbatim"] == "Retour valide"
