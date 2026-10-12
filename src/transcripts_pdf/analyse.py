import json
import re
import time
from copy import deepcopy
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


_REFERENCE = {
    "reference": {"$ref": "#/$defs/reference"},
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


class ErreurAnalysePdf(ValueError):
    def __init__(
        self,
        phase: str,
        code: str,
        duree_secondes: float,
        mesures: dict[str, str | int | float | None],
        message: str | None = None,
    ) -> None:
        self.phase = phase
        self.code = code
        self.duree_secondes = duree_secondes
        self.mesures = mesures
        super().__init__(message or code)


class ErreurValidationAnalyse(ValueError):
    def __init__(self, code: str, message: str = "Réponse d’analyse invalide.") -> None:
        self.code = code
        super().__init__(message)


class ServiceAnalysePdf:
    def __init__(
        self,
        albert: AdaptateurAlbert,
        prompts: dict[str, str],
        configuration_diagnostic: dict[str, str | int | float | None] | None = None,
        effort: str = "medium",
    ) -> None:
        self._albert = albert
        self._prompts = prompts
        self._configuration_diagnostic = configuration_diagnostic or {}
        self._effort = effort

    def analyser(
        self,
        type_source: str,
        contenu: str,
        contexte: str,
        roles: list[dict[str, str]],
        schema_version: str,
    ) -> AnalysePdf:
        details_tours = _tours_details(contenu)
        schema = deepcopy(_PRODUIT if type_source == "produit" else _BIZDEV)
        _restreindre_tours_schema(schema, details_tours)
        debut = time.monotonic()
        try:
            reponse = self._albert.completer_json_raisonnement_transcript(
                [
                    {"role": "system", "content": self._prompts[type_source]},
                    {
                        "role": "user",
                        "content": f"CONTEXTE ANONYMISE:\n{contexte}\nLOCUTEURS:\n{json.dumps(roles, ensure_ascii=False, separators=(',', ':'))}\nTOURS:\n{json.dumps(details_tours, ensure_ascii=False, separators=(',', ':'))}",
                    },
                ],
                f"analyse_transcript_{type_source}",
                schema,
                self._effort,
                cast(float, self._configuration_diagnostic.get("temperature", 0.0)),
                cast(float | None, self._configuration_diagnostic.get("top_p")),
            )
            diagnostic_completion = getattr(reponse, "diagnostic", {})
            mesures_completion = self._configuration_diagnostic | (
                diagnostic_completion
                if isinstance(diagnostic_completion, dict)
                else {}
            )
        except Exception as erreur:
            diagnostic_albert = getattr(erreur, "diagnostic", {})
            mesures = self._configuration_diagnostic | (
                diagnostic_albert if isinstance(diagnostic_albert, dict) else {}
            )
            code = mesures.pop("code_reponse", type(erreur).__name__)
            raise ErreurAnalysePdf(
                "appel_albert", str(code), round(time.monotonic() - debut, 3), mesures
            ) from None
        try:
            valeur = _lire_json(reponse, type_source)
        except ErreurValidationAnalyse as erreur:
            raise ErreurAnalysePdf(
                "lecture_json",
                erreur.code,
                round(time.monotonic() - debut, 3),
                mesures_completion,
                str(erreur),
            ) from None
        try:
            _valider_structure(valeur, type_source)
        except ErreurValidationAnalyse as erreur:
            raise ErreurAnalysePdf(
                "structure",
                erreur.code,
                round(time.monotonic() - debut, 3),
                mesures_completion,
                str(erreur),
            ) from None
        fonctionnalites = valeur["fonctionnalites"]
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
        try:
            for index, reference in enumerate(references, 1):
                reference_privee = reference.pop("reference")
                tour_id = reference_privee.get("tour_id")
                if not isinstance(tour_id, int) or isinstance(tour_id, bool):
                    raise _erreur_reference(
                        "tour_id_invalide", index, None, None, 0, debut
                    )
                locuteur = tours.get(tour_id)
                if locuteur is None:
                    raise _erreur_reference(
                        "tour_introuvable", index, tour_id, None, 0, debut
                    )
                texte_tour = _contenu_tour(contenu, tour_id)
                tokens = list(re.finditer(r"\S+", texte_tour))
                debut_token = reference_privee.get("token_debut")
                fin_token = reference_privee.get("token_fin")
                if (
                    not isinstance(debut_token, int)
                    or isinstance(debut_token, bool)
                    or not isinstance(fin_token, int)
                    or isinstance(fin_token, bool)
                ):
                    raise _erreur_reference(
                        "positions_type_invalide",
                        index,
                        tour_id,
                        locuteur,
                        len(tokens),
                        debut,
                    )
                if (
                    debut_token < 0
                    or fin_token < debut_token
                    or fin_token >= len(tokens)
                ):
                    raise _erreur_reference(
                        "positions_hors_limites",
                        index,
                        tour_id,
                        locuteur,
                        len(tokens),
                        debut,
                        debut_token,
                        fin_token,
                    )
                reference["verbatim"] = texte_tour[
                    tokens[debut_token].start() : tokens[fin_token].end()
                ]
                reference["speaker_id"] = locuteur
                reference["tour_id"] = tour_id
        except ErreurAnalysePdf as erreur:
            erreur.mesures = mesures_completion | erreur.mesures
            raise
        return AnalysePdf(
            schema_version, valeur, cast(list[dict[str, object]], fonctionnalites)
        )


def _lire_json(reponse: str, type_source: str) -> dict[str, Any]:
    try:
        valeur = json.loads(reponse)
    except json.JSONDecodeError:
        raise ErreurValidationAnalyse("json_invalide") from None
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
        raise ErreurValidationAnalyse("cles_racine_invalides")
    return cast(dict[str, Any], valeur)


def _valider_structure(valeur: dict[str, Any], type_source: str) -> None:
    if (
        not isinstance(valeur["resume"], str)
        or not isinstance(valeur["themes"], list)
        or any(not isinstance(item, str) for item in valeur["themes"])
    ):
        raise ErreurValidationAnalyse("types_racine_invalides")
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
        raise ErreurValidationAnalyse("listes_invalides")
    for item in valeur["fonctionnalites"]:
        if (
            not isinstance(item, dict)
            or set(item) != {"action", "reference"}
            or not isinstance(item["action"], str)
            or not _reference_privee_valide(item["reference"])
        ):
            raise ErreurValidationAnalyse(
                "fonctionnalite_invalide", "Fonctionnalité extraite invalide."
            )
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
                    "reference",
                }
                or item["type"] not in _TYPES
                or not isinstance(item["description"], str)
                or item["sentiment"] not in _SENTIMENTS
                or item["gravite"] not in (*_GRAVITES, None)
                or not _reference_privee_valide(item["reference"])
            ):
                raise ErreurValidationAnalyse(
                    "highlight_produit_invalide", "Extrait produit invalide."
                )
    else:
        for cle in listes[1:]:
            if any(
                not isinstance(item, dict)
                or set(item) != {"description", "reference"}
                or not isinstance(item["description"], str)
                or not _reference_privee_valide(item["reference"])
                for item in valeur[cle]
            ):
                raise ErreurValidationAnalyse(
                    "extraction_bizdev_invalide", "Extraction BizDev invalide."
                )


def _tours(contenu: str) -> dict[int, str]:
    return {
        cast(int, tour["tour_id"]): cast(str, tour["speaker_id"])
        for tour in _tours_details(contenu)
    }


def _erreur_reference(
    code: str,
    index: int,
    tour_id: int | None,
    locuteur: str | None,
    nombre_tokens: int,
    debut: float,
    token_debut: int | None = None,
    token_fin: int | None = None,
) -> ErreurAnalysePdf:
    mesures: dict[str, str | int | float | None] = {
        "reference_index": index,
        "tour_id": tour_id,
        "speaker_id": (
            locuteur if locuteur and re.fullmatch(r"SPEAKER_\d{2}", locuteur) else None
        ),
        "tokens_tour": nombre_tokens,
        "token_debut": token_debut,
        "token_fin": token_fin,
    }
    return ErreurAnalysePdf(
        "references",
        code,
        round(time.monotonic() - debut, 3),
        mesures,
        "Une référence d’analyse ne correspond pas au transcript.",
    )


def _restreindre_tours_schema(
    schema: dict[str, object], tours: list[dict[str, object]]
) -> None:
    branches = []
    for tour in tours:
        tokens = cast(list[list[object]], tour["tokens"])
        if tokens:
            tour_id = cast(int, tour["tour_id"])
            borne = len(tokens) - 1
            branches.append(
                _objet_champs(
                    {
                        "tour_id": {"type": "integer", "enum": [tour_id]},
                        "token_debut": {
                            "type": "integer",
                            "minimum": 0,
                            "maximum": borne,
                        },
                        "token_fin": {
                            "type": "integer",
                            "minimum": 0,
                            "maximum": borne,
                        },
                    }
                )
            )
    if not branches:
        raise ErreurValidationAnalyse("aucun_tour_citable")
    schema["$defs"] = {"reference": {"anyOf": branches}}


def _reference_privee_valide(reference: object) -> bool:
    return isinstance(reference, dict) and set(reference) == {
        "tour_id",
        "token_debut",
        "token_fin",
    }


def _tours_details(contenu: str) -> list[dict[str, object]]:
    labels = list(re.finditer(r"(?m)^\s*(SPEAKER_\d{2}):\s*", contenu))
    tours = []
    for index, match in enumerate(labels):
        texte = contenu[
            match.end() : labels[index + 1].start()
            if index + 1 < len(labels)
            else len(contenu)
        ].strip()
        tokens = list(re.finditer(r"\S+", texte))
        tours.append(
            {
                "tour_id": index + 1,
                "speaker_id": match[1],
                "token_max": len(tokens) - 1,
                "tokens": [
                    [token_id, token.group()]
                    for token_id, token in enumerate(tokens)
                ],
            }
        )
    return tours


def _contenu_tour(contenu: str, tour_id: int) -> str:
    labels = list(re.finditer(r"(?m)^\s*SPEAKER_\d{2}:\s*", contenu))
    if tour_id < 1 or tour_id > len(labels):
        return ""
    debut = labels[tour_id - 1].end()
    fin = labels[tour_id].start() if tour_id < len(labels) else len(contenu)
    return contenu[debut:fin].strip()
