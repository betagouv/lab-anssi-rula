import json
from typing import NamedTuple

from adaptateurs.albert import AdaptateurAlbert
from adaptateurs.exceptions import ReponseAlbertInvalide


class ProblemeValidationTranscript(NamedTuple):
    categorie: str
    element: str
    raison: str


class ValidationTranscript(NamedTuple):
    valide: bool
    problemes: list[ProblemeValidationTranscript]


class ReponseValidationTranscriptInvalide(ReponseAlbertInvalide):
    pass


_CATEGORIES = {
    "identite",
    "donnee_personnelle",
    "donnee_sensible",
    "information_technique",
    "technologie_ou_produit",
}

_SCHEMA: dict[str, object] = {
    "type": "object",
    "properties": {
        "valide": {"type": "boolean"},
        "problemes": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "categorie": {"type": "string", "enum": sorted(_CATEGORIES)},
                    "element": {"type": "string"},
                    "raison": {"type": "string"},
                },
                "required": ["categorie", "element", "raison"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["valide", "problemes"],
    "additionalProperties": False,
}


class ServiceValidationTranscript:
    def __init__(self, albert: AdaptateurAlbert, systeme_prompt: str) -> None:
        self._albert = albert
        self._systeme_prompt = systeme_prompt

    def valider(self, contenu: str) -> ValidationTranscript:
        reponse = self._albert.completer_json(
            [
                {"role": "system", "content": self._systeme_prompt},
                {"role": "user", "content": contenu},
            ],
            "validation_transcript",
            _SCHEMA,
        )
        try:
            valeur = json.loads(reponse)
        except json.JSONDecodeError as erreur:
            raise ReponseValidationTranscriptInvalide from erreur
        if not isinstance(valeur, dict) or set(valeur) != {"valide", "problemes"}:
            raise ReponseValidationTranscriptInvalide
        valide = valeur["valide"]
        problemes_bruts = valeur["problemes"]
        if type(valide) is not bool or not isinstance(problemes_bruts, list):
            raise ReponseValidationTranscriptInvalide
        problemes: list[ProblemeValidationTranscript] = []
        for probleme in problemes_bruts:
            if not isinstance(probleme, dict) or set(probleme) != {
                "categorie",
                "element",
                "raison",
            }:
                raise ReponseValidationTranscriptInvalide
            categorie = probleme["categorie"]
            element = probleme["element"]
            raison = probleme["raison"]
            if (
                not isinstance(categorie, str)
                or categorie not in _CATEGORIES
                or not isinstance(element, str)
                or not isinstance(raison, str)
            ):
                raise ReponseValidationTranscriptInvalide
            problemes.append(ProblemeValidationTranscript(categorie, element, raison))
        if valide != (not problemes):
            raise ReponseValidationTranscriptInvalide
        return ValidationTranscript(valide, problemes)
