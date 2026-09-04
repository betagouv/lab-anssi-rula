import pytest

from adaptateurs.albert import AdaptateurAlbert
from adaptateurs.exceptions import ErreurCommunicationAlbert
from validation_transcript.service import (
    ReponseValidationTranscriptInvalide,
    ServiceValidationTranscript,
)


class _AlbertDeTest(AdaptateurAlbert):
    def __init__(self, reponse: str | Exception) -> None:
        self.reponse = reponse
        self.messages_recus: list[list[dict[str, str]]] = []
        self.schema_recu: dict[str, object] | None = None

    def completer(
        self, messages: list[dict[str, str]], temperature: float = 0.0
    ) -> str:
        return ""

    def completer_json(
        self,
        messages: list[dict[str, str]],
        nom_schema: str,
        schema: dict[str, object],
        temperature: float = 0.0,
    ) -> str:
        self.messages_recus.append(messages)
        self.schema_recu = schema
        if isinstance(self.reponse, Exception):
            raise self.reponse
        return self.reponse

    def plonger(self, textes: list[str]) -> list[list[float]]:
        return []


class _AlbertAvecCompletionSimpleDeTest(AdaptateurAlbert):
    def completer(
        self, messages: list[dict[str, str]], temperature: float = 0.0
    ) -> str:
        return "{}"

    def plonger(self, textes: list[str]) -> list[list[float]]:
        return []


def _service(
    reponse: str | Exception,
) -> tuple[ServiceValidationTranscript, _AlbertDeTest]:
    albert = _AlbertDeTest(reponse)
    return ServiceValidationTranscript(albert, "prompt de validation"), albert


def test_accepte_un_transcript_conforme() -> None:
    service, albert = _service('{"valide":true,"problemes":[]}')

    resultat = service.valider("Un utilisateur décrit un besoin produit.")

    assert resultat.valide
    assert resultat.problemes == []
    assert (
        albert.messages_recus[-1][-1]["content"]
        == "Un utilisateur décrit un besoin produit."
    )
    assert albert.schema_recu is not None


def test_refuse_un_transcript_avec_tous_les_problemes() -> None:
    service, _ = _service(
        '{"valide":false,"problemes":[{"categorie":"identite","element":"Alice Martin","raison":"Nom complet d’une personne."},{"categorie":"technologie_ou_produit","element":"ProduitX","raison":"Nom de produit."}]}'
    )

    resultat = service.valider("Alice Martin utilise ProduitX.")

    assert not resultat.valide
    assert [p.raison for p in resultat.problemes] == [
        "Nom complet d’une personne.",
        "Nom de produit.",
    ]


def test_completion_json_par_defaut_utilise_la_completion_simple() -> None:
    albert = _AlbertAvecCompletionSimpleDeTest()

    assert albert.completer_json([], "schema", {}) == "{}"


@pytest.mark.parametrize(
    "reponse",
    [
        "",
        "pas du JSON",
        "[]",
        '{"valide":"oui","problemes":[]}',
        '{"valide":true,"problemes":[{"categorie":"identite","element":"Alice","raison":"Nom."}]}',
        '{"valide":false,"problemes":[]}',
        '{"valide":false,"problemes":[{"categorie":"identite","element":"Alice"}]}',
        '{"valide":false,"problemes":[{"categorie":"inconnue","element":"Alice","raison":"Nom."}]}',
        '{"valide":false,"problemes":[{"categorie":"identite","element":1,"raison":"Nom."}]}',
    ],
)
def test_refuse_une_reponse_albert_invalide(reponse: str) -> None:
    service, _ = _service(reponse)

    with pytest.raises(ReponseValidationTranscriptInvalide):
        service.valider("Un transcript.")


def test_propage_l_indisponibilite_d_albert() -> None:
    service, _ = _service(ErreurCommunicationAlbert())

    with pytest.raises(ErreurCommunicationAlbert):
        service.valider("Un transcript.")
