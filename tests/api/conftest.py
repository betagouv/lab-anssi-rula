from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from adaptateurs.albert import AdaptateurAlbert
from analyses.service import ServiceAnalyse
from api.analyses import fabrique_service_analyse
from api.fonctionnalites import fabrique_service_fonctionnalites
from api.idees import fabrique_service_idees
from api.identites import fabrique_depot_identites
from api.produits import fabrique_depot_produits
from api.transcripts import fabrique_depot_transcripts
from fonctionnalites.service import ServiceFonctionnalites
from idees.service import ServiceIdees
from infra.memoire.depot_analyses_transcripts import DepotAnalysesTranscriptsMemoire
from infra.memoire.depot_fonctionnalites_transcripts import DepotFonctionnalitesTranscriptsMemoire
from infra.memoire.depot_idees import DepotIdeesMemoire
from infra.memoire.depot_identites import DepotIdentitesMemoire
from infra.memoire.depot_produits import DepotProduitsMemoire
from infra.memoire.depot_transcripts import DepotTranscriptsMemoire
from serveur import app


class _AlbertAnalyseDeTest(AdaptateurAlbert):
    def completer(self, messages: list[dict[str, str]], temperature: float = 0.0) -> str:
        return "Analyse générée"


class _AlbertFonctionnalitesDeTest(AdaptateurAlbert):
    def completer(self, messages: list[dict[str, str]], temperature: float = 0.0) -> str:
        return '["Fonctionnalité A", "Fonctionnalité B"]'


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    depot_identites = DepotIdentitesMemoire()
    depot_produits = DepotProduitsMemoire()
    depot_transcripts = DepotTranscriptsMemoire()
    depot_analyses = DepotAnalysesTranscriptsMemoire()
    depot_fonctionnalites = DepotFonctionnalitesTranscriptsMemoire()
    depot_idees = DepotIdeesMemoire()
    service_analyse = ServiceAnalyse(depot_transcripts, depot_analyses, _AlbertAnalyseDeTest(), "prompt test")
    service_fonctionnalites = ServiceFonctionnalites(depot_transcripts, depot_fonctionnalites, _AlbertFonctionnalitesDeTest(), "prompt test")
    service_idees = ServiceIdees(depot=depot_idees)
    app.dependency_overrides[fabrique_depot_identites] = lambda: depot_identites
    app.dependency_overrides[fabrique_depot_produits] = lambda: depot_produits
    app.dependency_overrides[fabrique_depot_transcripts] = lambda: depot_transcripts
    app.dependency_overrides[fabrique_service_analyse] = lambda: service_analyse
    app.dependency_overrides[fabrique_service_fonctionnalites] = lambda: service_fonctionnalites
    app.dependency_overrides[fabrique_service_idees] = lambda: service_idees
    yield TestClient(app)
    app.dependency_overrides.clear()
