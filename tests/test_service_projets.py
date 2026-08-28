from datetime import date

import pytest

from projets.service import ProjetIntrouvable, ServiceScansProjets
from tests.adaptateurs.albert_de_test import AdaptateurAlbertDeTest
from tests.projets.depot_projets_de_test import DepotProjetsDeTest


def test_genere_un_scan_des_entretiens() -> None:
    depot = DepotProjetsDeTest()
    projet = depot.ajouter(1, "Recherche", "")
    depot.ajouter_entretien(projet.id, "A", date(2026, 8, 25), "B", "Contenu", "Note")
    service = ServiceScansProjets(depot, AdaptateurAlbertDeTest().avec_reponse("Scan"), "prompt")

    assert service.generer(projet.id).brouillon == "Scan"


def test_refuse_un_projet_absent() -> None:
    with pytest.raises(ProjetIntrouvable):
        ServiceScansProjets(DepotProjetsDeTest(), AdaptateurAlbertDeTest(), "prompt").generer(1)
