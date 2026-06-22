from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from adaptateurs.albert import AdaptateurAlbert
from analyses.service import ServiceAnalyse
from api.analyses import fabrique_service_analyse
from api.correspondances import fabrique_service_correspondance
from api.fonctionnalites import fabrique_service_fonctionnalites
from api.idees import fabrique_service_idees
from api.identites import fabrique_depot_identites
from api.produits import fabrique_depot_produits
from api.retours_bizdev import fabrique_service_retours_bizdev
from api.transcripts import fabrique_depot_transcripts
from correspondance.depot import Feature
from correspondance.service import ServiceCorrespondance
from fonctionnalites.service import ServiceFonctionnalites
from idees.service import ServiceIdees
from infra.memoire.depot_analyses_transcripts import DepotAnalysesTranscriptsMemoire
from infra.memoire.depot_correspondance import DepotCorrespondanceMemoire
from infra.memoire.depot_correspondances_calculees import DepotCorrespondancesCalculeesMemoire
from infra.memoire.depot_fonctionnalites_transcripts import DepotFonctionnalitesTranscriptsMemoire
from infra.memoire.depot_idees import DepotIdeesMemoire
from infra.memoire.depot_identites import DepotIdentitesMemoire
from infra.memoire.depot_produits import DepotProduitsMemoire
from infra.memoire.depot_retours_bizdev import DepotRetoursBizDevMemoire
from infra.memoire.depot_transcripts import DepotTranscriptsMemoire
from retours_bizdev.service import ServiceRetoursBizDev
from serveur import app

_FEATURES = [
    Feature("transcript", 1, "Accès prestataire", 1, "le prestataire n'a pas accès"),
    Feature("transcript", 2, "Accès spécifique prestataire", 2, "accès spécifique requis"),
    Feature("idee", 1, "Export PDF", None, None),
    Feature("retour_bizdev", 1, "Vue d'ensemble participants", None, "[SUPER ADMIN] — Vue d'ensemble"),
]
_EMBEDDINGS = {
    "Accès prestataire": [1.0, 0.0],
    "Accès spécifique prestataire": [0.99, 0.01],
    "Export PDF": [0.0, 1.0],
    "Vue d'ensemble participants": [0.0, -1.0],
}


class _AlbertAnalyseDeTest(AdaptateurAlbert):
    def completer(self, messages: list[dict[str, str]], temperature: float = 0.0) -> str:
        return "Analyse générée"

    def plonger(self, textes: list[str]) -> list[list[float]]:
        return []


class _AlbertFonctionnalitesDeTest(AdaptateurAlbert):
    def completer(self, messages: list[dict[str, str]], temperature: float = 0.0) -> str:
        return '[{"fonctionnalite": "Fonctionnalité A", "verbatim": "verbatim A"}, {"fonctionnalite": "Fonctionnalité B", "verbatim": "verbatim B"}]'

    def plonger(self, textes: list[str]) -> list[list[float]]:
        return []


class _AlbertEmbeddingsDeTest(AdaptateurAlbert):
    def completer(self, messages: list[dict[str, str]], temperature: float = 0.0) -> str:
        return "Libellé généré"

    def plonger(self, textes: list[str]) -> list[list[float]]:
        return [_EMBEDDINGS[t] for t in textes]


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    depot_identites = DepotIdentitesMemoire()
    depot_produits = DepotProduitsMemoire()
    depot_transcripts = DepotTranscriptsMemoire()
    depot_analyses = DepotAnalysesTranscriptsMemoire()
    depot_fonctionnalites = DepotFonctionnalitesTranscriptsMemoire()
    depot_idees = DepotIdeesMemoire()
    depot_retours_bizdev = DepotRetoursBizDevMemoire()
    service_analyse = ServiceAnalyse(depot_transcripts, depot_analyses, _AlbertAnalyseDeTest(), "prompt test")
    service_fonctionnalites = ServiceFonctionnalites(depot_transcripts, depot_fonctionnalites, _AlbertFonctionnalitesDeTest(), "prompt test")
    service_idees = ServiceIdees(depot=depot_idees)
    service_retours_bizdev = ServiceRetoursBizDev(depot=depot_retours_bizdev)
    service_correspondance = ServiceCorrespondance(DepotCorrespondanceMemoire(list(_FEATURES)), DepotCorrespondancesCalculeesMemoire(), _AlbertEmbeddingsDeTest(), 0.35, "prompt test")
    app.dependency_overrides[fabrique_depot_identites] = lambda: depot_identites
    app.dependency_overrides[fabrique_depot_produits] = lambda: depot_produits
    app.dependency_overrides[fabrique_depot_transcripts] = lambda: depot_transcripts
    app.dependency_overrides[fabrique_service_analyse] = lambda: service_analyse
    app.dependency_overrides[fabrique_service_fonctionnalites] = lambda: service_fonctionnalites
    app.dependency_overrides[fabrique_service_idees] = lambda: service_idees
    app.dependency_overrides[fabrique_service_retours_bizdev] = lambda: service_retours_bizdev
    app.dependency_overrides[fabrique_service_correspondance] = lambda: service_correspondance
    yield TestClient(app)
    app.dependency_overrides.clear()
