import json
import logging
import re
from typing import Callable, NamedTuple, TypedDict, cast
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
_JOURNAL = logging.getLogger("uvicorn.error")


class ErreurPreparationInvalide(ValueError):
    def __init__(
        self,
        code: str,
        message: str = "Réponse de préparation invalide.",
        champ: str | None = None,
        nombre_attendu: int | None = None,
        nombre_recu: int | None = None,
        type_recu: str | None = None,
    ) -> None:
        self.code = code
        self.champ = champ
        self.nombre_attendu = nombre_attendu
        self.nombre_recu = nombre_recu
        self.type_recu = type_recu
        super().__init__(message)


def _schema_preparation(
    speaker_ids: set[str], fragments: list["Fragment"]
) -> dict[str, object]:
    token_ids = sorted(
        {
            token_id
            for fragment in fragments
            for token_id in range(len(_tokeniser(fragment.contenu)))
        }
    )
    return {
        "type": "object",
        "properties": {
            "remplacements": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "categorie": {"type": "string", "enum": list(_CATEGORIES)},
                        "fragment_id": {
                            "type": "integer",
                            "enum": sorted(
                                {fragment.fragment_id for fragment in fragments}
                            ),
                        },
                        "token_debut": {"type": "integer", "enum": token_ids},
                        "token_fin": {"type": "integer", "enum": token_ids},
                    },
                    "required": [
                        "categorie",
                        "fragment_id",
                        "token_debut",
                        "token_fin",
                    ],
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


def _journaliser_groupe(
    albert: AdaptateurAlbert,
    numero: int,
    total: int,
    fragments: list["Fragment"],
    locuteurs: int,
    erreur: Exception | None,
    phase: str = "groupe",
    caracteres_serialises: int | None = None,
) -> None:
    metriques = getattr(albert, "metriques_dernier_flux", {})
    diagnostic: dict[str, object] = {
        "groupe": numero,
        "groupes": total,
        "caracteres_source": sum(len(fragment.contenu) for fragment in fragments),
        "caracteres_serialises": caracteres_serialises,
        "locuteurs": locuteurs,
        "exception": type(erreur).__name__ if erreur else None,
        "code_validation": getattr(erreur, "code", None),
        "champ": getattr(erreur, "champ", None),
        "nombre_attendu": getattr(erreur, "nombre_attendu", None),
        "nombre_recu": getattr(erreur, "nombre_recu", None),
        "type_recu": getattr(erreur, "type_recu", None),
        "phase": phase,
    }
    diagnostic.update(
        {
            cle: metriques[cle]
            for cle in (
                "modele",
                "budget_completion",
                "statut_http",
                "finish_reason",
                "duree_totale_s",
                "evenements",
                "raisonnement_caracteres",
                "contenu_caracteres",
                "request_id",
            )
            if isinstance(metriques, dict) and cle in metriques
        }
    )
    _JOURNAL.info("Diagnostic préparation transcript : %s", diagnostic)


class Remplacement(TypedDict):
    categorie: str
    fragment_id: int
    token_debut: int
    token_fin: int


class RemplacementResolu(TypedDict):
    valeur: str
    categorie: str
    champ: str
    debut: int
    fin: int


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
    offset_debut: int = 0


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
        progression: Callable[[str, int, int | None, int | None], None] | None = None,
    ) -> PreparationTranscript:
        if type_source not in {"produit", "bizdev"}:
            raise ValueError("Type de source invalide.")
        if progression:
            progression("extraction", 0, None, None)
        texte, date_source = extraire_pdf(nom_fichier, fichier)
        locuteurs_origine = anonymiser_locuteurs(texte)[1]
        identifiants = dict(locuteurs_origine)
        fragments = [
            fragment._replace(fragment_id=index)
            for index, fragment in enumerate(
                _fragments_transcript(texte, identifiants)
                + (_fragments_champ("contexte", contexte) if contexte else []),
                1,
            )
            if _tokeniser(fragment.contenu)
        ]
        groupes = _grouper_fragments(fragments)
        if progression:
            progression("anonymisation", 0, len(groupes), 1 if groupes else None)
        valeurs: list[PreparationLue] = []
        remplacements_resolus: list[RemplacementResolu] = []
        for numero_groupe, fragments_groupe in enumerate(groupes, 1):
            speakers_segment = {
                fragment.speaker_id
                for fragment in fragments_groupe
                if fragment.champ == "transcript" and fragment.speaker_id
            }
            phase = "appel_albert"
            fragments_json = json.dumps(
                [_serialiser_fragment(fragment) for fragment in fragments_groupe],
                ensure_ascii=False,
            )
            contenu_message = f"TYPE: {type_source}\nFRAGMENTS:\n{fragments_json}"
            caracteres_serialises = len(contenu_message)
            try:
                reponse = self._albert.completer_json_raisonnement_preparation(
                    [
                        {"role": "system", "content": self._prompt},
                        {
                            "role": "user",
                            "content": contenu_message,
                        },
                    ],
                    "preparation_transcript",
                    _schema_preparation(speakers_segment, fragments_groupe),
                    "high",
                )
                phase = "lecture_reponse"
                valeur = _lire_preparation(reponse)
                phase = "validation_locuteurs"
                if speakers_segment != {
                    locuteur["speaker_id"] for locuteur in valeur["locuteurs"]
                }:
                    raise ErreurPreparationInvalide(
                        "ensemble_speakers_inattendu",
                        champ="locuteurs",
                        nombre_attendu=len(speakers_segment),
                        nombre_recu=len(valeur["locuteurs"]),
                    )
                phase = "validation_remplacements"
                remplacements_resolus.extend(
                    _resoudre_remplacements(valeur["remplacements"], fragments_groupe)
                )
            except Exception as erreur:
                _journaliser_groupe(
                    self._albert,
                    numero_groupe,
                    len(groupes),
                    fragments_groupe,
                    len(speakers_segment),
                    erreur,
                    phase,
                    caracteres_serialises,
                )
                raise
            _journaliser_groupe(
                self._albert,
                numero_groupe,
                len(groupes),
                fragments_groupe,
                len(speakers_segment),
                None,
                caracteres_serialises=caracteres_serialises,
            )
            valeurs.append(valeur)
            if progression:
                progression(
                    "anonymisation",
                    numero_groupe,
                    len(groupes),
                    numero_groupe + 1 if numero_groupe < len(groupes) else None,
                )
        if progression:
            progression("finalisation", len(groupes), len(groupes), None)
        labels = locuteurs_origine
        try:
            remplacements = _positions_valides(remplacements_resolus, texte, contexte)
        except Exception as erreur:
            _journaliser_groupe(
                self._albert,
                len(groupes),
                len(groupes),
                groupes[-1],
                len(labels),
                erreur,
                "fusion_finale",
            )
            raise
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
            voix = votes.get(identifiant, [])
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
        raise ErreurPreparationInvalide("json_illisible") from erreur
    if not isinstance(valeur, dict) or set(valeur) != {"remplacements", "locuteurs"}:
        raise ErreurPreparationInvalide(
            "structure_premier_niveau",
            champ="racine",
            nombre_attendu=2,
            nombre_recu=len(valeur) if isinstance(valeur, dict) else None,
            type_recu=type(valeur).__name__,
        )
    if not isinstance(valeur["remplacements"], list):
        raise ErreurPreparationInvalide(
            "structure_remplacements",
            champ="remplacements",
            type_recu=type(valeur["remplacements"]).__name__,
        )
    if isinstance(valeur["locuteurs"], dict):
        if any(
            not isinstance(details, dict) for details in valeur["locuteurs"].values()
        ):
            raise ErreurPreparationInvalide(
                "structure_locuteurs",
                champ="locuteurs",
                type_recu="details_non_objet",
            )
        valeur["locuteurs"] = [
            {"speaker_id": speaker_id, **details}
            for speaker_id, details in valeur["locuteurs"].items()
        ]
    if not isinstance(valeur["locuteurs"], list):
        raise ErreurPreparationInvalide(
            "structure_locuteurs",
            champ="locuteurs",
            type_recu=type(valeur["locuteurs"]).__name__,
        )
    for item in valeur["remplacements"]:
        if (
            not isinstance(item, dict)
            or set(item) != {"categorie", "fragment_id", "token_debut", "token_fin"}
            or not isinstance(item["categorie"], str)
            or item["categorie"] not in _CATEGORIES
            or not isinstance(item["fragment_id"], int)
            or isinstance(item["fragment_id"], bool)
            or not isinstance(item["token_debut"], int)
            or isinstance(item["token_debut"], bool)
            or not isinstance(item["token_fin"], int)
            or isinstance(item["token_fin"], bool)
            or item["token_debut"] < 0
            or item["token_fin"] < item["token_debut"]
        ):
            raise ErreurPreparationInvalide(
                "structure_remplacements",
                champ="remplacements",
                nombre_attendu=4,
                nombre_recu=len(item) if isinstance(item, dict) else None,
                type_recu=type(item).__name__,
            )
    for item in valeur["locuteurs"]:
        if (
            not isinstance(item, dict)
            or set(item) != {"speaker_id", "role", "justification"}
            or not isinstance(item["speaker_id"], str)
            or not re.fullmatch(r"SPEAKER_[0-9]{2}", item["speaker_id"])
            or not isinstance(item["justification"], str)
            or item["role"] not in _ROLES
        ):
            raise ErreurPreparationInvalide(
                "structure_locuteurs",
                champ="locuteurs",
                nombre_attendu=3,
                nombre_recu=len(item) if isinstance(item, dict) else None,
                type_recu=type(item).__name__,
            )
    return cast(PreparationLue, valeur)


def _fragments_champ(champ: str, texte: str) -> list[Fragment]:
    pas = _TAILLE_FRAGMENT - _CHEVAUCHEMENT_FRAGMENT
    return [
        Fragment(
            champ, index, texte[debut : debut + _TAILLE_FRAGMENT], offset_debut=debut
        )
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
    blocs: list[tuple[str | None, str, int]] = []
    debut = 0
    for index, repere in enumerate(reperes):
        if repere.start() > debut:
            blocs.append((None, texte[debut : repere.start()], debut))
        fin = reperes[index + 1].start() if index + 1 < len(reperes) else len(texte)
        blocs.append((identifiants[repere[1]], texte[repere.end() : fin], repere.end()))
        debut = fin
    if not reperes:
        blocs.append((None, texte, 0))
    fragments = []
    tour_id = 0
    pas = _TAILLE_FRAGMENT - _CHEVAUCHEMENT_FRAGMENT
    for speaker_id, contenu, offset in blocs:
        for fragment_id, debut_fragment in enumerate(range(0, len(contenu), pas)):
            fragments.append(
                Fragment(
                    "transcript",
                    fragment_id,
                    contenu[debut_fragment : debut_fragment + _TAILLE_FRAGMENT],
                    tour_id,
                    speaker_id,
                    offset + debut_fragment,
                )
            )
        tour_id += 1
    return fragments


def _decouper(texte: str, par_tour: bool = False) -> list[str]:
    return [
        texte[debut : debut + _TAILLE_FRAGMENT]
        for debut in range(0, len(texte), _TAILLE_FRAGMENT)
    ]


def _tokeniser(texte: str) -> list[tuple[str, int, int]]:
    return [
        (match.group(), match.start(), match.end())
        for match in re.finditer(r"\w+|[^\w\s]", texte)
    ]


def _serialiser_fragment(fragment: Fragment) -> dict[str, object]:
    return {
        "champ": fragment.champ,
        "fragment_id": fragment.fragment_id,
        "tour_id": fragment.tour_id,
        "speaker_id": fragment.speaker_id,
        "contenu": fragment.contenu,
        "tokens": [
            {"token_id": index, "contenu": token}
            for index, (token, _, _) in enumerate(_tokeniser(fragment.contenu))
        ],
    }


def _resoudre_remplacements(
    remplacements: list[Remplacement], fragments: list[Fragment]
) -> list[RemplacementResolu]:
    fragments_par_id = {fragment.fragment_id: fragment for fragment in fragments}
    resultat = []
    for remplacement in remplacements:
        fragment = fragments_par_id.get(remplacement["fragment_id"])
        if fragment is None:
            raise ErreurPreparationInvalide(
                "fragment_absent", champ="fragment_id", nombre_attendu=1, nombre_recu=0
            )
        tokens = _tokeniser(fragment.contenu)
        debut_token = remplacement["token_debut"]
        fin_token = remplacement["token_fin"]
        if debut_token >= len(tokens) or fin_token >= len(tokens):
            raise ErreurPreparationInvalide(
                "token_absent",
                champ="tokens",
                nombre_attendu=len(tokens),
                nombre_recu=fin_token,
            )
        debut_local = tokens[debut_token][1]
        fin_local = tokens[fin_token][2]
        resultat.append(
            {
                "valeur": fragment.contenu[debut_local:fin_local],
                "categorie": remplacement["categorie"],
                "champ": fragment.champ,
                "debut": fragment.offset_debut + debut_local,
                "fin": fragment.offset_debut + fin_local,
            }
        )
    return cast(list[RemplacementResolu], resultat)


def _positions_valides(
    remplacements: list[RemplacementResolu], texte: str, contexte: str
) -> list[tuple[RemplacementResolu, int, int]]:
    champs = {"transcript": texte, "contexte": contexte}
    positions: list[tuple[RemplacementResolu, int, int]] = []
    valeurs: set[tuple[str, int, int, str]] = set()
    categories: dict[tuple[str, int, int], str] = {}
    for remplacement in remplacements:
        champ = remplacement["champ"]
        valeur = remplacement["valeur"]
        debut = remplacement["debut"]
        fin = remplacement["fin"]
        if (
            champ not in champs
            or not valeur
            or debut < 0
            or fin <= debut
            or fin > len(champs[champ])
            or champs[champ][debut:fin] != valeur
        ):
            raise ErreurPreparationInvalide("remplacement_invalide")
        cle = (champ, debut, fin)
        if cle in categories and categories[cle] != remplacement["categorie"]:
            raise ErreurPreparationInvalide(
                "categories_incompatibles",
                "Une valeur a plusieurs catégories d’anonymisation.",
            )
        categories[cle] = remplacement["categorie"]
        deduplication = (*cle, remplacement["categorie"])
        if deduplication in valeurs:
            continue
        valeurs.add(deduplication)
        positions.append((remplacement, debut, fin))
    triees = sorted(
        positions,
        key=lambda element: (
            element[0]["champ"],
            element[1],
            -(element[2] - element[1]),
        ),
    )
    resultat: list[tuple[RemplacementResolu, int, int]] = []
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
            raise ErreurPreparationInvalide(
                "categories_incompatibles",
                "Les valeurs d’anonymisation ont des catégories incompatibles.",
            )
        if any(
            precedent[1] <= position[1] and precedent[2] >= position[2]
            for precedent in chevauchements
        ):
            if all(
                precedent[0]["categorie"] == position[0]["categorie"]
                for precedent in chevauchements
            ):
                continue
        if chevauchements:
            raise ErreurPreparationInvalide(
                "chevauchement", "Les valeurs d’anonymisation se chevauchent."
            )
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
