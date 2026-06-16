from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from api.identites import fabrique_depot_identites
from api.produits import fabrique_depot_produits
from api.transcripts import fabrique_depot_transcripts
from infra.memoire.depot_identites import DepotIdentitesMemoire
from infra.memoire.depot_produits import DepotProduitsMemoire
from infra.memoire.depot_transcripts import DepotTranscriptsMemoire
from serveur import app


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    depot_identites = DepotIdentitesMemoire()
    depot_produits = DepotProduitsMemoire()
    depot_transcripts = DepotTranscriptsMemoire()
    app.dependency_overrides[fabrique_depot_identites] = lambda: depot_identites
    app.dependency_overrides[fabrique_depot_produits] = lambda: depot_produits
    app.dependency_overrides[fabrique_depot_transcripts] = lambda: depot_transcripts
    yield TestClient(app)
    app.dependency_overrides.clear()
