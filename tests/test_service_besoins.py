from adaptateurs.albert import AdaptateurAlbert
from besoins.service import ServiceBesoinsDetectes
from fonctionnalites.service import ServiceFonctionnalites
from infra.memoire.depot_besoins_detectes import DepotBesoinsDetectesMemoire
from infra.memoire.depot_fonctionnalites_transcripts import DepotFonctionnalitesTranscriptsMemoire
from infra.memoire.depot_idees import DepotIdeesMemoire
from infra.memoire.depot_retours_bizdev import DepotRetoursBizDevMemoire
from infra.memoire.depot_transcripts import DepotTranscriptsMemoire


class _AlbertSelonReponse(AdaptateurAlbert):
    def __init__(self, reponse: str) -> None:
        self.reponse = reponse

    def completer(self, messages: list[dict[str, str]], temperature: float = 0.0) -> str:
        return self.reponse

    def plonger(self, textes: list[str]) -> list[list[float]]:
        return []


def _service(albert: AdaptateurAlbert) -> ServiceBesoinsDetectes:
    transcripts = DepotTranscriptsMemoire()
    fonctionnalites = DepotFonctionnalitesTranscriptsMemoire()
    service_fonctionnalites = ServiceFonctionnalites(transcripts, fonctionnalites, albert, "prompt")
    return ServiceBesoinsDetectes(
        depot=DepotBesoinsDetectesMemoire(),
        depot_transcripts=transcripts,
        depot_fonctionnalites=fonctionnalites,
        service_fonctionnalites=service_fonctionnalites,
        depot_idees=DepotIdeesMemoire(),
        depot_retours=DepotRetoursBizDevMemoire(),
        albert=albert,
        prompt_featurebase="prompt featurebase",
        prompt_bizdev="prompt bizdev",
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
