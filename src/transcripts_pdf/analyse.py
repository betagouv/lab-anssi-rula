import json
import re
from typing import Any, NamedTuple, cast

from adaptateurs.albert import AdaptateurAlbert

_TYPES = (
    "pain_point",
    "confusion_erreur_usage",
    "comportement_contournement",
    "besoin",
    "demande_solution",
    "motivation_contexte",
    "ce_qui_marche",
    "autre",
)
_SENTIMENTS = ("positif", "neutre", "negatif")
_GRAVITES = ("bloquant", "genant", "mineur")


def _objet_champs(champs: dict[str, object]) -> dict[str, object]:
    return {
        "type": "object",
        "properties": champs,
        "required": list(champs),
        "additionalProperties": False,
    }


def _liste_texte() -> dict[str, object]:
    return {"type": "array", "items": {"type": "string"}}


def _verbatim() -> dict[str, object]:
    return {"type": "string"}


_REFERENCE = {
    "verbatim": _verbatim(),
    "tour_id": {"type": "integer", "minimum": 1},
    "speaker_id": {"type": "string", "pattern": "^SPEAKER_[0-9]{2}$"},
}
_FONCTIONNALITE = _objet_champs({"action": {"type": "string"}, **_REFERENCE})
_FAIT = _objet_champs({"description": {"type": "string"}, **_REFERENCE})
_PRODUIT = _objet_champs(
    {
        "resume": {"type": "string"},
        "themes": _liste_texte(),
        "highlights": {
            "type": "array",
            "items": _objet_champs(
                {
                    "type": {"type": "string", "enum": list(_TYPES)},
                    "description": {"type": "string"},
                    "sentiment": {
                        "type": "string",
                        "enum": list(_SENTIMENTS),
                    },
                    "gravite": {
                        "type": ["string", "null"],
                        "enum": [*_GRAVITES, None],
                    },
                    **_REFERENCE,
                }
            ),
        },
        "fonctionnalites": {"type": "array", "items": _FONCTIONNALITE},
    }
)
_BIZDEV = _objet_champs(
    {
        "resume": {"type": "string"},
        "themes": _liste_texte(),
        "enjeux": {"type": "array", "items": _FAIT},
        "besoins_globaux": {"type": "array", "items": _FAIT},
        "freins": {"type": "array", "items": _FAIT},
        "motivations": {"type": "array", "items": _FAIT},
        "opportunites": {"type": "array", "items": _FAIT},
        "propositions": {"type": "array", "items": _FAIT},
        "signaux_positifs": {"type": "array", "items": _FAIT},
        "suites_evoquees": {"type": "array", "items": _FAIT},
        "fonctionnalites": {"type": "array", "items": _FONCTIONNALITE},
    }
)


class AnalysePdf(NamedTuple):
    schema_version: str
    contenu: dict[str, object]
    fonctionnalites: list[dict[str, object]]


class ServiceAnalysePdf:
    def __init__(self, albert: AdaptateurAlbert, prompts: dict[str, str]) -> None:
        self._albert = albert
        self._prompts = prompts

    def analyser(
        self,
        type_source: str,
        contenu: str,
        contexte: str,
        roles: list[dict[str, str]],
        schema_version: str,
    ) -> AnalysePdf:
        schema = _PRODUIT if type_source == "produit" else _BIZDEV
        reponse = self._albert.completer_json_raisonnement(
            [
                {"role": "system", "content": self._prompts[type_source]},
                {
                    "role": "user",
                    "content": f"CONTEXTE ANONYMISE:\n{contexte}\nLOCUTEURS:\n{json.dumps(roles, ensure_ascii=False)}\nTOURS:\n{json.dumps(_tours_details(contenu), ensure_ascii=False)}",
                },
            ],
            f"analyse_transcript_{type_source}",
            schema,
            "high",
        )
        valeur = _lire_json(reponse, type_source)
        fonctionnalites = valeur["fonctionnalites"]
        _valider_structure(valeur, type_source)
        tours = _tours(contenu)
        references = list(valeur.get("highlights", [])) + fonctionnalites
        references.extend(
            item
            for cle in (
                "enjeux",
                "besoins_globaux",
                "freins",
                "motivations",
                "opportunites",
                "propositions",
                "signaux_positifs",
                "suites_evoquees",
            )
            for item in valeur.get(cle, [])
        )
        for reference in references:
            if (
                not isinstance(reference, dict)
                or not isinstance(reference.get("verbatim"), str)
                or not isinstance(reference.get("tour_id"), int)
                or tours.get(reference["tour_id"]) != reference.get("speaker_id")
                or reference["verbatim"]
                not in _contenu_tour(contenu, reference["tour_id"])
            ):
                raise ValueError(
                    "Une référence d’analyse ne correspond pas au transcript."
                )
        return AnalysePdf(
            schema_version, valeur, cast(list[dict[str, object]], fonctionnalites)
        )


def _lire_json(reponse: str, type_source: str) -> dict[str, Any]:
    try:
        valeur = json.loads(reponse)
    except json.JSONDecodeError as erreur:
        raise ValueError("Réponse d’analyse invalide.") from erreur
    champs = (
        {"resume", "themes", "highlights", "fonctionnalites"}
        if type_source == "produit"
        else {
            "resume",
            "themes",
            "enjeux",
            "besoins_globaux",
            "freins",
            "motivations",
            "opportunites",
            "propositions",
            "signaux_positifs",
            "suites_evoquees",
            "fonctionnalites",
        }
    )
    if not isinstance(valeur, dict) or set(valeur) != champs:
        raise ValueError("Réponse d’analyse invalide.")
    return cast(dict[str, Any], valeur)


def _valider_structure(valeur: dict[str, Any], type_source: str) -> None:
    if (
        not isinstance(valeur["resume"], str)
        or not isinstance(valeur["themes"], list)
        or any(not isinstance(item, str) for item in valeur["themes"])
    ):
        raise ValueError("Réponse d’analyse invalide.")
    listes = (
        ("fonctionnalites", "highlights")
        if type_source == "produit"
        else (
            "fonctionnalites",
            "enjeux",
            "besoins_globaux",
            "freins",
            "motivations",
            "opportunites",
            "propositions",
            "signaux_positifs",
            "suites_evoquees",
        )
    )
    if any(not isinstance(valeur[cle], list) for cle in listes):
        raise ValueError("Réponse d’analyse invalide.")
    for item in valeur["fonctionnalites"]:
        if (
            not isinstance(item, dict)
            or set(item) != {"action", "verbatim", "tour_id", "speaker_id"}
            or not isinstance(item["action"], str)
        ):
            raise ValueError("Fonctionnalité extraite invalide.")
    if type_source == "produit":
        for item in valeur["highlights"]:
            if (
                not isinstance(item, dict)
                or set(item)
                != {
                    "type",
                    "description",
                    "sentiment",
                    "gravite",
                    "verbatim",
                    "tour_id",
                    "speaker_id",
                }
                or item["type"] not in _TYPES
                or not isinstance(item["description"], str)
                or item["sentiment"] not in _SENTIMENTS
                or item["gravite"] not in (*_GRAVITES, None)
            ):
                raise ValueError("Extrait produit invalide.")
    else:
        for cle in listes[1:]:
            if any(
                not isinstance(item, dict)
                or set(item) != {"description", "verbatim", "tour_id", "speaker_id"}
                or not isinstance(item["description"], str)
                for item in valeur[cle]
            ):
                raise ValueError("Extraction BizDev invalide.")


def _tours(contenu: str) -> dict[int, str]:
    return {
        cast(int, tour["tour_id"]): cast(str, tour["speaker_id"])
        for tour in _tours_details(contenu)
    }


def _tours_details(contenu: str) -> list[dict[str, object]]:
    labels = list(re.finditer(r"(?m)^\s*(SPEAKER_\d{2}):\s*", contenu))
    return [
        {
            "tour_id": index + 1,
            "speaker_id": match[1],
            "contenu": contenu[
                match.end() : labels[index + 1].start()
                if index + 1 < len(labels)
                else len(contenu)
            ].strip(),
        }
        for index, match in enumerate(labels)
    ]


def _contenu_tour(contenu: str, tour_id: int) -> str:
    labels = list(re.finditer(r"(?m)^\s*SPEAKER_\d{2}:\s*", contenu))
    if tour_id < 1 or tour_id > len(labels):
        return ""
    debut = labels[tour_id - 1].end()
    fin = labels[tour_id].start() if tour_id < len(labels) else len(contenu)
    return contenu[debut:fin].strip()
