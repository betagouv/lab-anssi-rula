from datetime import date, datetime

import pytest

from besoins.dependances import DependancesBesoins
from besoins.depot import BesoinDetecte
from besoins.service import ServiceBesoinsDetectes, SourceBesoinInconnue
from fonctionnalites.service import ServiceFonctionnalites
from infra.memoire.depot_besoins_detectes import DepotBesoinsDetectesMemoire
from infra.memoire.depot_fonctionnalites_transcripts import (
    DepotFonctionnalitesTranscriptsMemoire,
)
from infra.memoire.depot_idees import DepotIdeesMemoire
from infra.memoire.depot_retours_bizdev import DepotRetoursBizDevMemoire
from infra.memoire.depot_transcripts import DepotTranscriptsMemoire
from adaptateurs.albert import AdaptateurAlbert


class _AlbertSelonReponse(AdaptateurAlbert):
    def __init__(self, reponse: str) -> None:
        self.reponse = reponse

    def completer(
        self, messages: list[dict[str, str]], temperature: float = 0.0
    ) -> str:
        return self.reponse

    def plonger(self, textes: list[str]) -> list[list[float]]:
        return []


def _service(albert: AdaptateurAlbert) -> ServiceBesoinsDetectes:
    transcripts = DepotTranscriptsMemoire()
    fonctionnalites = DepotFonctionnalitesTranscriptsMemoire()
    service_fonctionnalites = ServiceFonctionnalites(
        transcripts, fonctionnalites, albert, "prompt"
    )
    return ServiceBesoinsDetectes(
        dependances=DependancesBesoins(
            depot=DepotBesoinsDetectesMemoire(),
            depot_transcripts=transcripts,
            depot_fonctionnalites=fonctionnalites,
            service_fonctionnalites=service_fonctionnalites,
            depot_idees=DepotIdeesMemoire(),
            depot_retours=DepotRetoursBizDevMemoire(),
        ),
        albert=albert,
        prompts=("prompt featurebase", "prompt bizdev"),
    )


def test_nom_generique_accepte_objet_json() -> None:
    service = _service(_AlbertSelonReponse('{"fonctionnalite":"Export sécurisé"}'))
    assert service._nom_generique("prompt", "texte") == "Export sécurisé"


def test_nom_generique_accepte_chaine_json() -> None:
    service = _service(_AlbertSelonReponse('"Export sécurisé"'))
    assert service._nom_generique("prompt", "texte") == "Export sécurisé"


def test_nom_generique_conserve_une_reponse_brute() -> None:
    service = _service(_AlbertSelonReponse("Export sécurisé"))
    assert service._nom_generique("prompt", "texte") == "Export sécurisé"


def test_depot_besoins_restaure_un_snapshot() -> None:
    depot = DepotBesoinsDetectesMemoire()
    ancien = BesoinDetecte(
        7, "transcript", 1, "texte", "nom", None, 1, "extrait", datetime.now(), 1
    )
    depot.restaurer([ancien], 1)
    assert depot.lister(produit_id=1) == [ancien]
    service = _service(_AlbertSelonReponse(""))
    service.restaurer([], 1)
    assert service.remplacer("transcript", [], 1) == []


def test_preparer_transcripts_inclut_les_transcripts_du_produit() -> None:
    service = _service(
        _AlbertSelonReponse('[{"fonctionnalite":"Export", "verbatim":"export"}]')
    )
    service._depot_transcripts.ajouter(1, 3, date(2026, 8, 27), "Je veux exporter")

    assert service.preparer("transcript", 3) == [(1, "Export", "Export", "export", 1)]


def test_preparer_refuse_une_source_inconnue() -> None:
    with pytest.raises(SourceBesoinInconnue):
        _service(_AlbertSelonReponse("")).preparer("inconnue")
