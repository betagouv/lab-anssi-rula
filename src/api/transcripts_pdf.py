from concurrent.futures import Executor, ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone
from hashlib import sha256
import hmac
import logging
from pathlib import Path
import secrets
import time
from typing import Literal
from urllib.parse import urlsplit
from uuid import uuid4

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    Response,
    UploadFile,
)
from pydantic import BaseModel, ConfigDict, Field, model_validator

from adaptateurs.albert import AdaptateurAlbertReel
from api.produits import fabrique_depot_produits
from produits.depot import DepotProduits
from adaptateurs.exceptions import DelaiAlbertDepasse, ReponseAlbertInvalide
from configuration import charge_configuration
from infra.postgres.depot_liste_blanche import DepotListeBlanchePostgres
from infra.postgres.depot_transcripts_pdf import DepotTranscriptsPdfPostgres
from transcripts_pdf.depot import (
    DepotTranscriptsPdf,
    SourceTranscriptPdf,
)
from transcripts_pdf.extraction import ErreurPdf, TAILLE_MAXIMALE
from transcripts_pdf.export import generer_pdf
from transcripts_pdf.noms import nom_pseudonymise
from transcripts_pdf.orchestration import (
    ServiceTranscriptsPdf,
    SourcePdfInvalide,
)
from transcripts_pdf.service import (
    ErreurPreparationInvalide,
    OccurrencePseudonymisation,
    Locuteur,
    ServicePreparationTranscript,
)

routeur = APIRouter()
_JOURNAL = logging.getLogger(__name__)
_EXECUTEUR_PREPARATION = ThreadPoolExecutor(max_workers=1)
_EXECUTEUR_GROUPES_PREPARATION = ThreadPoolExecutor(
    max_workers=charge_configuration().albert.parallelisme_anonymisation
)
_PREPARATIONS: dict[str, dict] = {}
_TTL_PREPARATION = timedelta(minutes=30)
_PROMPT = Path(__file__).parent.parent / "prompts"
_ERREUR_PREPARATION_INVALIDE = (
    "Une réponse d’anonymisation incomplète ou incohérente a empêché de produire "
    "un brouillon fiable. Réessayez l’import ; si le problème persiste, "
    "contactez le support."
)


class LocuteurBody(BaseModel):
    identifiant: str
    role: Literal["interne", "externe", "indetermine"]
    justification: str
    nom_affiche: str = ""


class SourcePdfBody(BaseModel):
    preparation_id: str | None = Field(default=None, pattern=r"^[0-9a-f]{32}$")
    type_source: Literal["produit", "bizdev"]
    nom_source: str
    produit_id: int
    date_entretien: date | None
    contenu: str
    contexte: str = ""
    locuteurs: list[LocuteurBody]


class MasqueRelectureBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    identifiant: str = Field(pattern=r"^[0-9a-f-]{36}$")
    categorie: Literal[
        "identite",
        "coordonnees",
        "organisation",
        "secret",
        "donnee_sensible",
        "technologie_ou_produit",
    ]
    valeur_anonyme: str = Field(max_length=100)
    actif: bool


class PlageRelectureBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    identifiant: str = Field(pattern=r"^[0-9a-f-]{36}$")
    masque_identifiant: str = Field(pattern=r"^[0-9a-f-]{36}$")
    champ: Literal["transcript", "contexte"]
    debut: int = Field(ge=0)
    fin: int = Field(gt=0)

    @model_validator(mode="after")
    def verifier_plage(self) -> "PlageRelectureBody":
        if self.fin <= self.debut:
            raise ValueError("La plage de relecture est invalide.")
        return self


class InstantaneRelectureBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    masques: list[MasqueRelectureBody] = Field(max_length=20000)
    plages: list[PlageRelectureBody] = Field(max_length=50000)


class EtatRelectureBody(InstantaneRelectureBody):
    selection: str | None = Field(default=None, pattern=r"^[0-9a-f-]{36}$")
    annulations: list[InstantaneRelectureBody] = Field(max_length=100)
    retablissements: list[InstantaneRelectureBody] = Field(max_length=100)


class LocuteurRelectureBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    identifiant: str = Field(pattern=r"^SPEAKER_\d{2,}$")
    role: Literal["interne", "externe", "indetermine"]
    nom_affiche: str = Field(max_length=200)


class MiseAJourPreparationBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    etat_relecture: EtatRelectureBody
    locuteurs: list[LocuteurRelectureBody] = Field(max_length=500)
    date_entretien: date | None


def fabrique_depot_transcripts_pdf() -> DepotTranscriptsPdf:
    return DepotTranscriptsPdfPostgres(charge_configuration().base_de_donnees)


def fabrique_service_preparation_pdf() -> ServicePreparationTranscript:
    return ServicePreparationTranscript(
        None,
        (_PROMPT / "anonymisation_transcript.md").read_text(),
        executeur=_EXECUTEUR_GROUPES_PREPARATION,
        fabrique_albert=lambda: AdaptateurAlbertReel(charge_configuration().albert),
        depot_liste_blanche=DepotListeBlanchePostgres(
            charge_configuration().base_de_donnees
        ),
    )


def fabrique_service_transcripts_pdf(
    depot: DepotTranscriptsPdf = Depends(fabrique_depot_transcripts_pdf),
) -> ServiceTranscriptsPdf:
    return ServiceTranscriptsPdf(depot)


def _verifier_produit(produit_id: int, depot: DepotProduits) -> None:
    if not any(
        produit.id == produit_id and produit.nom in {"MSS", "MSC"}
        for produit in depot.lister()
    ):
        raise HTTPException(
            status_code=422, detail="Le produit MSS ou MSC est invalide."
        )


def fabrique_executeur_preparation() -> Executor:
    return _EXECUTEUR_PREPARATION


def _nom_cookie(identifiant: str) -> str:
    return f"rula_preparation_{identifiant}"


def _verifier_origine(request: Request) -> None:
    origine = request.headers.get("origin", "")
    valeur = urlsplit(origine)
    if (
        valeur.scheme not in {"http", "https"}
        or valeur.netloc != request.headers.get("host")
        or valeur.path not in {"", "/"}
        or valeur.query
        or valeur.fragment
    ):
        raise HTTPException(
            status_code=403,
            detail="Origine invalide.",
            headers={"Cache-Control": "no-store"},
        )


def _obtenir_preparation_autorisee(
    identifiant: str, request: Request, response: Response
) -> dict:
    response.headers["Cache-Control"] = "no-store"
    _nettoyer_preparations()
    preparation = _PREPARATIONS.get(identifiant)
    secret = request.cookies.get(_nom_cookie(identifiant), "")
    if preparation is None or not hmac.compare_digest(
        preparation["empreinte_cookie"], sha256(secret.encode()).hexdigest()
    ):
        raise HTTPException(
            status_code=404,
            detail="Préparation expirée ou introuvable.",
            headers={"Cache-Control": "no-store"},
        )
    preparation["expire"] = datetime.now(timezone.utc) + _TTL_PREPARATION
    return preparation


@routeur.post("/transcripts-pdf/preparation", status_code=202)
async def preparer(
    request: Request,
    response: Response,
    type_source: Literal["produit", "bizdev"] = Form(),
    produit_id: int = Form(),
    contexte: str = Form(""),
    fichier: UploadFile = File(),
    service: ServicePreparationTranscript = Depends(fabrique_service_preparation_pdf),
    executeur: Executor = Depends(fabrique_executeur_preparation),
    depot_produits: DepotProduits = Depends(fabrique_depot_produits),
) -> dict:
    response.headers["Cache-Control"] = "no-store"
    _verifier_origine(request)
    _verifier_produit(produit_id, depot_produits)
    _nettoyer_preparations()
    if (
        sum(
            preparation["statut"] == "en_cours"
            for preparation in _PREPARATIONS.values()
        )
        >= 2
    ):
        raise HTTPException(status_code=429, detail="Trop de préparations en cours.")
    contenu = await fichier.read(TAILLE_MAXIMALE + 1)
    identifiant = uuid4().hex
    secret = secrets.token_urlsafe(32)
    _PREPARATIONS[identifiant] = {
        "statut": "en_cours",
        "type_source": type_source,
        "produit_id": produit_id,
        "empreinte_cookie": sha256(secret.encode()).hexdigest(),
        "expire": datetime.now(timezone.utc) + _TTL_PREPARATION,
        "soumis_monotonic": time.monotonic(),
        "progression": {
            "phase": "en_attente",
            "groupes_termines": 0,
            "groupes_total": None,
            "groupes_en_cours": [],
        },
    }
    executeur.submit(
        _executer_preparation,
        identifiant,
        service,
        fichier.filename or "transcript.pdf",
        contenu,
        type_source,
        contexte,
        produit_id,
    )
    response.set_cookie(
        _nom_cookie(identifiant),
        secret,
        httponly=True,
        samesite="strict",
        secure=charge_configuration().rula.secure_cookie,
        path="/api/transcripts-pdf",
    )
    return {
        "identifiant": identifiant,
        "statut": "en_cours",
        "progression": _progression_publique(_PREPARATIONS[identifiant]),
    }


@routeur.get("/transcripts-pdf/preparation/{identifiant}")
def obtenir_preparation(identifiant: str, request: Request, response: Response) -> dict:
    preparation = _obtenir_preparation_autorisee(identifiant, request, response)
    if preparation["statut"] == "echec":
        return {
            "statut": "echec",
            "erreur": preparation["erreur"],
            "progression": _progression_publique(preparation),
        }
    if preparation["statut"] == "termine":
        resultat = dict(preparation["resultat"])
        if "etat_relecture" in preparation:
            resultat["etat_relecture"] = preparation["etat_relecture"]
            resultat["date_entretien"] = preparation["date_entretien"]
            locuteurs = {
                locuteur["identifiant"]: locuteur
                for locuteur in preparation["locuteurs"]
            }
            resultat["locuteurs"] = [
                {**locuteur, **locuteurs.get(locuteur["identifiant"], {})}
                for locuteur in resultat["locuteurs"]
            ]
        return {
            "statut": "termine",
            "progression": _progression_publique(preparation),
            **resultat,
        }
    return {
        "statut": "en_cours",
        "progression": _progression_publique(preparation),
    }


@routeur.put("/transcripts-pdf/preparation/{identifiant}/relecture")
def mettre_a_jour_relecture(
    identifiant: str,
    body: MiseAJourPreparationBody,
    request: Request,
    response: Response,
) -> dict:
    response.headers["Cache-Control"] = "no-store"
    _verifier_origine(request)
    preparation = _obtenir_preparation_autorisee(identifiant, request, response)
    if preparation["statut"] != "termine":
        raise HTTPException(
            status_code=409,
            detail="Préparation non terminée.",
            headers={"Cache-Control": "no-store"},
        )
    locuteurs_initiaux = preparation["resultat"]["locuteurs"]
    identifiants = {locuteur["identifiant"] for locuteur in locuteurs_initiaux}
    locuteurs = [locuteur.model_dump() for locuteur in body.locuteurs]
    if {locuteur["identifiant"] for locuteur in locuteurs} != identifiants:
        raise HTTPException(
            status_code=422,
            detail="Liste de locuteurs invalide.",
            headers={"Cache-Control": "no-store"},
        )
    preparation.update(
        etat_relecture=body.etat_relecture.model_dump(),
        locuteurs=locuteurs,
        date_entretien=body.date_entretien,
    )
    return {"statut": "enregistre"}


@routeur.delete("/transcripts-pdf/preparation/{identifiant}", status_code=204)
def abandonner_preparation(
    identifiant: str, request: Request, response: Response
) -> None:
    response.headers["Cache-Control"] = "no-store"
    _verifier_origine(request)
    _obtenir_preparation_autorisee(identifiant, request, response)
    del _PREPARATIONS[identifiant]
    response.delete_cookie(
        _nom_cookie(identifiant),
        path="/api/transcripts-pdf",
        secure=charge_configuration().rula.secure_cookie,
        httponly=True,
        samesite="strict",
    )


def _progression_publique(preparation: dict) -> dict:
    return {
        **preparation["progression"],
        "duree_secondes": round(time.monotonic() - preparation["soumis_monotonic"], 1),
    }


def _executer_preparation(
    jeton: str,
    service: ServicePreparationTranscript,
    nom_fichier: str,
    fichier: bytes,
    type_source: str,
    contexte: str,
    produit_id: int,
) -> None:
    phase_diagnostic = "en_attente"

    def actualiser_progression(
        phase: str,
        groupes_termines: int,
        groupes_total: int | None,
        groupes_en_cours: list[int],
    ) -> None:
        nonlocal phase_diagnostic
        if phase != "echec":
            phase_diagnostic = phase
        if jeton in _PREPARATIONS:
            _PREPARATIONS[jeton]["progression"].update(
                {
                    "phase": phase,
                    "groupes_termines": groupes_termines,
                    "groupes_total": groupes_total,
                    "groupes_en_cours": groupes_en_cours,
                }
            )

    try:
        preparation = service.preparer(
            nom_fichier, fichier, type_source, contexte, actualiser_progression
        )
        resultat = {
            "type_source": preparation.type_source,
            "produit_id": produit_id,
            "nom_source": preparation.nom_source,
            "date_entretien": preparation.date_entretien,
            "contenu": preparation.contenu,
            "contexte": preparation.contexte,
            "contenu_original": preparation.contenu_original,
            "contexte_original": preparation.contexte_original,
            "locuteurs": [locuteur._asdict() for locuteur in preparation.locuteurs],
            "remplacements": [
                remplacement._asdict() for remplacement in preparation.remplacements
            ],
            "conflits_categories_fusionnes": preparation.conflits_categories_fusionnes,
            "occurrences": [
                _occurrence_dict(
                    occurrence,
                    preparation.contenu_original,
                    preparation.contexte_original,
                )
                for occurrence in preparation.occurrences
            ],
        }
        if jeton in _PREPARATIONS:
            actualiser_progression(
                "termine",
                _PREPARATIONS[jeton]["progression"]["groupes_termines"],
                _PREPARATIONS[jeton]["progression"]["groupes_total"],
                [],
            )
            _PREPARATIONS[jeton].update(statut="termine", resultat=resultat)
    except ErreurPdf as erreur:
        _journaliser_echec_preparation(jeton, erreur, phase_diagnostic)
        if jeton in _PREPARATIONS:
            _PREPARATIONS[jeton]["progression"].update(
                phase="echec", groupes_en_cours=[]
            )
            _PREPARATIONS[jeton].update(statut="echec", erreur=str(erreur))
    except Exception as erreur:
        _journaliser_echec_preparation(jeton, erreur, phase_diagnostic)
        if jeton in _PREPARATIONS:
            _PREPARATIONS[jeton]["progression"].update(
                phase="echec", groupes_en_cours=[]
            )
            _PREPARATIONS[jeton].update(
                statut="echec",
                erreur=(
                    DelaiAlbertDepasse.detail_par_defaut
                    if isinstance(erreur, DelaiAlbertDepasse)
                    else _ERREUR_PREPARATION_INVALIDE
                    if isinstance(
                        erreur, (ErreurPreparationInvalide, ReponseAlbertInvalide)
                    )
                    else "La préparation du transcript a échoué."
                ),
            )


def _occurrence_dict(
    occurrence: OccurrencePseudonymisation,
    contenu_original: str,
    contexte_original: str,
) -> dict[str, object]:
    resultat: dict[str, object] = occurrence._asdict()
    source = contenu_original if occurrence.champ == "transcript" else contexte_original
    resultat["debut"] = len(source[: occurrence.debut].encode("utf-16-le")) // 2
    resultat["fin"] = len(source[: occurrence.fin].encode("utf-16-le")) // 2
    return resultat


def _journaliser_echec_preparation(jeton: str, erreur: Exception, phase: str) -> None:
    champs = [
        f"jeton_hash={sha256(jeton.encode()).hexdigest()[:16]}",
        f"phase={phase}",
        f"exception_type={type(erreur).__name__}",
    ]
    if isinstance(erreur, ErreurPreparationInvalide):
        champs.extend(
            f"{nom}={valeur}"
            for nom, valeur in (
                ("code", erreur.code),
                ("champ", erreur.champ),
                ("nombre_attendu", erreur.nombre_attendu),
                ("nombre_recu", erreur.nombre_recu),
            )
            if valeur is not None
        )
    if isinstance(erreur, DelaiAlbertDepasse):
        champs.append("code=delai_albert_depasse")
        champs.extend(
            f"{nom}={erreur.diagnostic[nom]}"
            for nom in (
                "groupe",
                "delai_tentative_s",
                "duree_tentative_s",
                "duree_totale_s",
                "tentatives",
                "retry_cause_type",
            )
            if erreur.diagnostic.get(nom) is not None
        )
        champs.append(f'message="{DelaiAlbertDepasse.detail_par_defaut}"')
    _JOURNAL.error("Échec préparation transcript PDF %s", " ".join(champs))


def _nettoyer_preparations() -> None:
    maintenant = datetime.now(timezone.utc)
    for jeton in [
        jeton
        for jeton, valeur in _PREPARATIONS.items()
        if valeur["expire"] <= maintenant
    ]:
        del _PREPARATIONS[jeton]


@routeur.post("/transcripts-pdf", status_code=201)
def confirmer(
    body: SourcePdfBody,
    request: Request,
    response: Response,
    service: ServiceTranscriptsPdf = Depends(fabrique_service_transcripts_pdf),
    depot_produits: DepotProduits = Depends(fabrique_depot_produits),
) -> dict:
    if body.preparation_id is None:
        raise HTTPException(status_code=422, detail="La préparation est obligatoire.")
    _verifier_produit(body.produit_id, depot_produits)
    preparation = _obtenir_preparation_autorisee(body.preparation_id, request, response)
    if (
        preparation["statut"] != "termine"
        or preparation["type_source"] != body.type_source
        or preparation["produit_id"] != body.produit_id
    ):
        raise HTTPException(
            status_code=422,
            detail="Le produit ou le type ne correspond pas à la préparation.",
        )
    try:
        source = service.confirmer(
            body.type_source,
            body.nom_source,
            body.produit_id,
            body.date_entretien,
            body.contenu,
            body.contexte,
            [Locuteur(**locuteur.model_dump()) for locuteur in body.locuteurs],
        )
    except SourcePdfInvalide as erreur:
        raise HTTPException(status_code=422, detail=str(erreur)) from erreur
    del _PREPARATIONS[body.preparation_id]
    response.delete_cookie(
        _nom_cookie(body.preparation_id),
        path="/api/transcripts-pdf",
        secure=charge_configuration().rula.secure_cookie,
        httponly=True,
        samesite="strict",
    )
    return _source_dict(source)


@routeur.get("/transcripts-pdf/produits/{produit_id}")
def lister(
    produit_id: int,
    service: ServiceTranscriptsPdf = Depends(fabrique_service_transcripts_pdf),
    depot_produits: DepotProduits = Depends(fabrique_depot_produits),
) -> list[dict]:
    _verifier_produit(produit_id, depot_produits)
    return [_source_dict(source) for source in service.lister(produit_id)]


@routeur.get("/transcripts-pdf/{transcript_id}/pdf")
def exporter_pdf(
    transcript_id: int,
    depot: DepotTranscriptsPdf = Depends(fabrique_depot_transcripts_pdf),
) -> Response:
    source = depot.obtenir(transcript_id)
    if source is None:
        raise HTTPException(404, headers={"Cache-Control": "no-store"})
    nom = nom_pseudonymise(source.nom_source)
    return Response(
        content=generer_pdf(source),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{nom}"',
            "Cache-Control": "no-store",
            "X-Content-Type-Options": "nosniff",
        },
    )


@routeur.get("/transcripts-pdf/{transcript_id}")
def obtenir(
    transcript_id: int,
    service: ServiceTranscriptsPdf = Depends(fabrique_service_transcripts_pdf),
) -> dict:
    source = service.obtenir(transcript_id)
    if source is None:
        raise HTTPException(status_code=404)
    return _source_dict(source)


@routeur.put("/transcripts-pdf/{transcript_id}")
def modifier(
    transcript_id: int,
    body: SourcePdfBody,
    service: ServiceTranscriptsPdf = Depends(fabrique_service_transcripts_pdf),
) -> dict:
    source = service.obtenir(transcript_id)
    if (
        source is None
        or source.type_source != body.type_source
        or source.produit_id != body.produit_id
    ):
        raise HTTPException(status_code=404)
    try:
        modifie = service.modifier(
            transcript_id,
            body.date_entretien,
            body.contenu,
            body.contexte,
            [Locuteur(**locuteur.model_dump()) for locuteur in body.locuteurs],
        )
    except SourcePdfInvalide as erreur:
        raise HTTPException(status_code=422, detail=str(erreur)) from erreur
    if modifie is None:
        raise HTTPException(status_code=404)
    return _source_dict(modifie)


@routeur.delete("/transcripts-pdf/{transcript_id}", status_code=204)
def supprimer(
    transcript_id: int,
    service: ServiceTranscriptsPdf = Depends(fabrique_service_transcripts_pdf),
) -> None:
    if not service.supprimer(transcript_id):
        raise HTTPException(status_code=404)


def _source_dict(source: SourceTranscriptPdf) -> dict:
    return source._replace(nom_source=nom_pseudonymise(source.nom_source))._asdict()
