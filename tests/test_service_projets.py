from datetime import date

import pytest

from projets.service import CorpusProjetModifie, ProjetIntrouvable, ServiceScansProjets
from projets.depot import DepotProjets, SourceAnalyseProjet
from tests.adaptateurs.albert_de_test import AdaptateurAlbertDeTest
from tests.projets.depot_projets_de_test import DepotProjetsDeTest


class AdaptateurAlbertModifieCorpusDeTest(AdaptateurAlbertDeTest):
    def __init__(self, depot: DepotProjetsDeTest, projet_id: int) -> None:
        super().__init__()
        self._depot = depot
        self._projet_id = projet_id

    def completer(
        self, messages: list[dict[str, str]], temperature: float = 0.0
    ) -> str:
        self._depot.ajouter_entretien(
            self._projet_id, "C", date(2026, 8, 26), "B", "Suite", ""
        )
        return "Scan obsolète"


def test_genere_un_scan_des_entretiens() -> None:
    depot = DepotProjetsDeTest()
    projet = depot.ajouter(1, "Recherche", "")
    depot.ajouter_entretien(projet.id, "A", date(2026, 8, 25), "B", "Contenu", "Note")
    service = ServiceScansProjets(
        depot, AdaptateurAlbertDeTest().avec_reponse("Scan"), "prompt"
    )

    assert service.generer(projet.id).brouillon == "Scan"


def test_refuse_un_projet_absent() -> None:
    with pytest.raises(ProjetIntrouvable):
        ServiceScansProjets(
            DepotProjetsDeTest(), AdaptateurAlbertDeTest(), "prompt"
        ).generer(1)


def test_depot_refuse_un_scan_calcule_sur_une_revision_obsolete() -> None:
    depot = DepotProjetsDeTest()
    projet = depot.ajouter(1, "Recherche", "")
    revision = projet.revision_corpus
    depot.ajouter_entretien(projet.id, "A", date(2026, 8, 25), "B", "Contenu", "Note")

    assert (
        depot.enregistrer_scan_si_revision(projet.id, revision, "Scan obsolète") is None
    )
    assert DepotProjets.enregistrer_scan_si_revision(depot, 999, 1, "Scan") is None


def test_formate_une_source_pdf_avec_locuteurs_et_contexte() -> None:
    source = SourceAnalyseProjet(
        1,
        "produit",
        None,
        date(2026, 8, 26),
        None,
        "SPEAKER_01: Texte",
        "",
        "Contexte",
        [{"identifiant": "SPEAKER_01", "role": "externe"}],
    )

    contenu = ServiceScansProjets._formater_source(source)

    assert "SPEAKER_01: externe" in contenu
    assert "Contexte" in contenu
    assert "SPEAKER_01: Texte" in contenu


def test_service_refuse_un_scan_si_le_corpus_change_pendant_le_calcul() -> None:
    depot = DepotProjetsDeTest()
    projet = depot.ajouter(1, "Recherche", "")
    depot.ajouter_entretien(projet.id, "A", date(2026, 8, 25), "B", "Contenu", "Note")
    with pytest.raises(CorpusProjetModifie):
        ServiceScansProjets(
            depot, AdaptateurAlbertModifieCorpusDeTest(depot, projet.id), "prompt"
        ).generer(projet.id)
