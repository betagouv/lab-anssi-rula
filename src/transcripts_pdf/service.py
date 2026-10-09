import json
import re
from typing import NamedTuple, TypedDict, cast
from uuid import uuid4

from adaptateurs.albert import AdaptateurAlbert
from transcripts_pdf.extraction import (
    appliquer_remplacements_positions,
    anonymiser_locuteurs,
    extraire_pdf,
)

_CATEGORIES = (
    "identite",
    "coordonnees",
    "organisation",
    "secret",
    "donnee_sensible",
    "technologie_ou_produit",
)
_ROLES = ("interne", "externe", "indetermine")
_TAILLE_FRAGMENT = 2000
_CHEVAUCHEMENT_FRAGMENT = 100


def _schema_preparation(speaker_ids: set[str]) -> dict[str, object]:
    return {
        "type": "object",
        "properties": {
            "remplacements": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "valeur": {"type": "string"},
                        "categorie": {"type": "string", "enum": list(_CATEGORIES)},
                        "champ": {"type": "string", "enum": ["transcript", "contexte"]},
                    },
                    "required": ["valeur", "categorie", "champ"],
                    "additionalProperties": False,
                },
            },
            "locuteurs": {
                "type": "object",
                "properties": {
                    speaker_id: {
                        "type": "object",
                        "properties": {
                            "role": {"type": "string", "enum": list(_ROLES)},
                            "justification": {"type": "string"},
                        },
                        "required": ["role", "justification"],
                        "additionalProperties": False,
                    }
                    for speaker_id in sorted(speaker_ids)
                },
                "required": sorted(speaker_ids),
                "additionalProperties": False,
            },
        },
        "required": ["remplacements", "locuteurs"],
        "additionalProperties": False,
    }


class Locuteur(NamedTuple):
    identifiant: str
    role: str
    justification: str


class Remplacement(TypedDict):
    valeur: str
    categorie: str
    champ: str


class LocuteurPrepare(TypedDict):
    speaker_id: str
    role: str
    justification: str


class Fragment(NamedTuple):
    champ: str
    fragment_id: int
    contenu: str
    tour_id: int | None = None
    speaker_id: str | None = None


class RemplacementVisible(NamedTuple):
    valeur_originale: str
    valeur_anonyme: str
    categorie: str
    champ: str


class PreparationLue(TypedDict):
    remplacements: list[Remplacement]
    locuteurs: list[LocuteurPrepare]


class PreparationTranscript(NamedTuple):
    type_source: str
    nom_source: str
    date_entretien: str | None
    contenu: str
    contexte: str
    locuteurs: list[Locuteur]
    remplacements: list[RemplacementVisible]


class ServicePreparationTranscript:
    def __init__(self, albert: AdaptateurAlbert, prompt: str) -> None:
        self._albert = albert
        self._prompt = prompt

    def preparer(
        self,
        nom_fichier: str,
        fichier: bytes,
        type_source: str,
        contexte: str,
    ) -> PreparationTranscript:
        if type_source not in {"produit", "bizdev"}:
            raise ValueError("Type de source invalide.")
        texte, date_source = extraire_pdf(nom_fichier, fichier)
        locuteurs_origine = anonymiser_locuteurs(texte)[1]
        identifiants = dict(locuteurs_origine)
        fragments = _grouper_fragments(
            _fragments_transcript(texte, identifiants)
            + (_fragments_champ("contexte", contexte) if contexte else [])
        )
        valeurs: list[PreparationLue] = []
        for fragments_groupe in fragments:
            speakers_segment = {
                fragment.speaker_id
                for fragment in fragments_groupe
                if fragment.champ == "transcript" and fragment.speaker_id
            }
            reponse = self._albert.completer_json_raisonnement_preparation(
                [
                    {"role": "system", "content": self._prompt},
                    {
                        "role": "user",
                        "content": f"TYPE: {type_source}\nFRAGMENTS:\n{json.dumps([fragment._asdict() for fragment in fragments_groupe], ensure_ascii=False)}",
                    },
                ],
                "preparation_transcript",
                _schema_preparation(speakers_segment),
                "high",
            )
            valeur = _lire_preparation(reponse)
            if speakers_segment != {
                locuteur["speaker_id"] for locuteur in valeur["locuteurs"]
            }:
                raise ValueError("Réponse de préparation invalide.")
            for remplacement in valeur["remplacements"]:
                if not any(
                    fragment.champ == remplacement["champ"]
                    and remplacement["valeur"] in fragment.contenu
                    for fragment in fragments_groupe
                ):
                    raise ValueError("Réponse de préparation invalide.")
            valeurs.append(valeur)
        labels = locuteurs_origine
        remplacements = _positions_valides(
            [
                remplacement
                for valeur in valeurs
                for remplacement in valeur["remplacements"]
            ],
            texte,
            contexte,
        )
        compteurs: dict[str, int] = {}
        anonymises: dict[tuple[str, str], str] = {}
        positions_texte: list[tuple[int, int, str]] = []
        positions_contexte: list[tuple[int, int, str]] = []
        remplacements_visibles: list[RemplacementVisible] = []
        visibles: set[tuple[str, str, str]] = set()
        for remplacement, debut, fin in remplacements:
            categorie = remplacement["categorie"]
            cle = (categorie, remplacement["valeur"])
            if cle not in anonymises:
                compteurs[categorie] = compteurs.get(categorie, 0) + 1
                anonymises[cle] = f"[{categorie.upper()}_{compteurs[categorie]:02d}]"
            anonyme = anonymises[cle]
            positions = (
                positions_texte
                if remplacement["champ"] == "transcript"
                else positions_contexte
            )
            positions.append((debut, fin, anonyme))
            visible = (remplacement["valeur"], categorie, remplacement["champ"])
            if visible not in visibles:
                visibles.add(visible)
                remplacements_visibles.append(
                    RemplacementVisible(
                        remplacement["valeur"],
                        anonyme,
                        categorie,
                        remplacement["champ"],
                    )
                )
        contenu = appliquer_remplacements_positions(texte, positions_texte)
        contenu, _ = anonymiser_locuteurs(contenu)
        contexte_anonyme = appliquer_remplacements_positions(
            contexte, positions_contexte
        )
        votes: dict[str, list[LocuteurPrepare]] = {}
        for valeur in valeurs:
            for locuteur in valeur["locuteurs"]:
                votes.setdefault(locuteur["speaker_id"], []).append(locuteur)
        originaux_par_id = {anonyme: original for original, anonyme in labels}
        locuteurs = []
        for _, identifiant in labels:
            voix = votes[identifiant]
            roles_connus = {
                vote["role"] for vote in voix if vote["role"] != "indetermine"
            }
            if originaux_par_id[identifiant] == "None" or len(roles_connus) > 1:
                role = "indetermine"
                justification = (
                    "La diarisation est inconnue."
                    if originaux_par_id[identifiant] == "None"
                    else "Les extraits ne permettent pas de déterminer le rôle."
                )
            elif roles_connus:
                role = next(iter(roles_connus))
                justification = f"Les extraits indiquent un rôle {role}."
            else:
                role = "indetermine"
                justification = "Les extraits ne permettent pas de déterminer le rôle."
            locuteurs.append(Locuteur(identifiant, role, justification))
        return PreparationTranscript(
            type_source,
            _nom_source(
                nom_fichier,
                type_source,
                date_source.isoformat() if date_source else "sans-date",
            ),
            date_source.isoformat() if date_source else None,
            contenu,
            contexte_anonyme,
            locuteurs,
            remplacements_visibles,
        )


def _lire_preparation(reponse: str) -> PreparationLue:
    try:
        valeur = json.loads(reponse)
    except json.JSONDecodeError as erreur:
        raise ValueError("Réponse de préparation invalide.") from erreur
    if not isinstance(valeur, dict) or set(valeur) != {"remplacements", "locuteurs"}:
        raise ValueError("Réponse de préparation invalide.")
    if not isinstance(valeur["remplacements"], list):
        raise ValueError("Réponse de préparation invalide.")
    if isinstance(valeur["locuteurs"], dict):
        valeur["locuteurs"] = [
            {"speaker_id": speaker_id, **details}
            for speaker_id, details in valeur["locuteurs"].items()
        ]
    if not isinstance(valeur["locuteurs"], list):
        raise ValueError("Réponse de préparation invalide.")
    for item in valeur["remplacements"]:
        if (
            not isinstance(item, dict)
            or set(item) != {"valeur", "categorie", "champ"}
            or not isinstance(item["valeur"], str)
            or not item["valeur"]
            or not isinstance(item["categorie"], str)
            or item["categorie"] not in _CATEGORIES
            or not isinstance(item["champ"], str)
            or item["champ"] not in {"transcript", "contexte"}
        ):
            raise ValueError("Réponse de préparation invalide.")
    for item in valeur["locuteurs"]:
        if (
            not isinstance(item, dict)
            or set(item) != {"speaker_id", "role", "justification"}
            or not isinstance(item["speaker_id"], str)
            or not re.fullmatch(r"SPEAKER_[0-9]{2}", item["speaker_id"])
            or not isinstance(item["justification"], str)
            or item["role"] not in _ROLES
        ):
            raise ValueError("Réponse de préparation invalide.")
    return cast(PreparationLue, valeur)


def _fragments_champ(champ: str, texte: str) -> list[Fragment]:
    pas = _TAILLE_FRAGMENT - _CHEVAUCHEMENT_FRAGMENT
    return [
        Fragment(champ, index, texte[debut : debut + _TAILLE_FRAGMENT])
        for index, debut in enumerate(range(0, len(texte), pas))
    ]


def _grouper_fragments(fragments: list[Fragment]) -> list[list[Fragment]]:
    groupes: list[list[Fragment]] = []
    groupe: list[Fragment] = []
    caracteres = 0
    for fragment in fragments:
        if groupe and caracteres + len(fragment.contenu) > _TAILLE_FRAGMENT:
            groupes.append(groupe)
            groupe = []
            caracteres = 0
        groupe.append(fragment)
        caracteres += len(fragment.contenu)
    if groupe:
        groupes.append(groupe)
    return groupes


def _fragments_transcript(texte: str, identifiants: dict[str, str]) -> list[Fragment]:
    reperes = list(re.finditer(r"(?m)^([A-Za-z]{7}_[0-9]{2}|None):[ \t]*", texte))
    blocs: list[tuple[str | None, str]] = []
    debut = 0
    for index, repere in enumerate(reperes):
        if repere.start() > debut:
            blocs.append((None, texte[debut : repere.start()]))
        fin = reperes[index + 1].start() if index + 1 < len(reperes) else len(texte)
        blocs.append((identifiants[repere[1]], texte[repere.end() : fin]))
        debut = fin
    if not reperes:
        blocs.append((None, texte))
    fragments = []
    tour_id = 0
    pas = _TAILLE_FRAGMENT - _CHEVAUCHEMENT_FRAGMENT
    for speaker_id, contenu in blocs:
        for fragment_id, debut_fragment in enumerate(range(0, len(contenu), pas)):
            fragments.append(
                Fragment(
                    "transcript",
                    fragment_id,
                    contenu[debut_fragment : debut_fragment + _TAILLE_FRAGMENT],
                    tour_id,
                    speaker_id,
                )
            )
        tour_id += 1
    return fragments


def _decouper(texte: str, par_tour: bool = False) -> list[str]:
    return [
        texte[debut : debut + _TAILLE_FRAGMENT]
        for debut in range(0, len(texte), _TAILLE_FRAGMENT)
    ]


def _positions_valides(
    remplacements: list[Remplacement], texte: str, contexte: str
) -> list[tuple[Remplacement, int, int]]:
    champs = {"transcript": texte, "contexte": contexte}
    positions: list[tuple[Remplacement, int, int]] = []
    valeurs: set[tuple[str, str, str]] = set()
    categories: dict[tuple[str, str], str] = {}
    for remplacement in remplacements:
        champ = remplacement["champ"]
        valeur = remplacement["valeur"]
        if champ not in champs or not valeur:
            raise ValueError("Réponse de préparation invalide.")
        cle = (champ, valeur)
        if cle in categories and categories[cle] != remplacement["categorie"]:
            raise ValueError("Une valeur a plusieurs catégories d’anonymisation.")
        categories[cle] = remplacement["categorie"]
        deduplication = (*cle, remplacement["categorie"])
        if deduplication in valeurs:
            continue
        valeurs.add(deduplication)
        texte_champ = champs[champ]
        occurrences = []
        debut = texte_champ.find(valeur)
        while debut >= 0:
            occurrences.append((debut, debut + len(valeur)))
            debut = texte_champ.find(valeur, debut + 1)
        if not occurrences:
            raise ValueError("Réponse de préparation invalide.")
        positions.extend((remplacement, debut, fin) for debut, fin in occurrences)
    triees = sorted(
        positions,
        key=lambda element: (
            element[0]["champ"],
            element[1],
            -(element[2] - element[1]),
        ),
    )
    resultat: list[tuple[Remplacement, int, int]] = []
    for position in triees:
        chevauchements = [
            precedent
            for precedent in resultat
            if precedent[0]["champ"] == position[0]["champ"]
            and precedent[1] < position[2]
            and position[1] < precedent[2]
        ]
        if any(
            precedent[0]["categorie"] != position[0]["categorie"]
            for precedent in chevauchements
        ):
            raise ValueError(
                "Les valeurs d’anonymisation ont des catégories incompatibles."
            )
        if any(
            precedent[1] <= position[1] and precedent[2] >= position[2]
            for precedent in chevauchements
        ):
            continue
        if chevauchements:
            raise ValueError("Les valeurs d’anonymisation se chevauchent.")
        resultat.append(position)
    return resultat


def _nom_source(nom_fichier: str, type_source: str, date_source: str) -> str:
    nom_canonique = re.fullmatch(
        r"reunion-_[a-z]{3}-[a-z]{4}-[a-z]{3}_-du-\d{4}-\d{2}-\d{2}-a-\d{2}_\d{2}\.pdf",
        nom_fichier,
        re.IGNORECASE,
    )
    return (
        nom_fichier
        if nom_canonique
        else f"transcript-{type_source}-{date_source}-{uuid4().hex[:8]}.pdf"
    )
