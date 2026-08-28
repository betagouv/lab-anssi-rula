from datetime import date
from pathlib import Path
from typing import cast

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from adaptateurs.albert import AdaptateurAlbertReel
from api.produits import fabrique_depot_produits
from configuration import charge_configuration
from infra.postgres.depot_projets import DepotProjetsPostgres
from infra.postgres.depot_analyse import DepotAnalysePostgres
from projets.analyse import (
    DepotAnalyse,
    EtapeAbsente,
    EtapeInaccessible,
    ProjetSansEntretien,
    ServiceAnalyseProjet,
)
from projets.depot import DepotProjets
from projets.service import (
    ProjetDejaExistant,
    ProjetIntrouvable,
    ServiceScansProjets,
)
from produits.depot import DepotProduits
from validation_transcript.service import ServiceValidationTranscript

routeur = APIRouter()
_prompt = (Path(__file__).parent.parent / "prompts" / "scan_projet.md").read_text()


def fabrique_depot_projets() -> DepotProjets:  # pragma: no cover
    return DepotProjetsPostgres(charge_configuration().base_de_donnees)


def fabrique_depot_analyse() -> DepotAnalyse:  # pragma: no cover
    return DepotAnalysePostgres(charge_configuration().base_de_donnees)


def fabrique_service_analyse_projet(
    projets: DepotProjets = Depends(fabrique_depot_projets),
    analyses: DepotAnalyse = Depends(fabrique_depot_analyse),
) -> ServiceAnalyseProjet:  # pragma: no cover
    return ServiceAnalyseProjet(
        projets, analyses, AdaptateurAlbertReel(charge_configuration().albert)
    )


def fabrique_service_scan(
    depot: DepotProjets = Depends(fabrique_depot_projets),
) -> ServiceScansProjets:  # pragma: no cover
    return ServiceScansProjets(
        depot, AdaptateurAlbertReel(charge_configuration().albert), _prompt
    )


def fabrique_service_validation() -> ServiceValidationTranscript:  # pragma: no cover
    from api.transcripts import fabrique_service_validation_transcript

    return fabrique_service_validation_transcript()


class NouveauProjet(BaseModel):
    produit_id: int
    nom: str
    brief: str = ""


class NouvelEntretien(BaseModel):
    participant: str
    date_entretien: date
    moderateur: str
    contenu: str
    note_moderateur: str = ""
    confirmation: bool


class NouveauScan(BaseModel):
    contenu: str


class NouveauProjetSource(BaseModel):
    nom: str
    brief: str = ""


class EntretienSource(BaseModel):
    participant: str
    date_entretien: date
    moderateur: str
    contenu: str
    note_moderateur: str = ""


class NouvelleSource(BaseModel):
    projet_id: int | None = None
    nouveau_projet: NouveauProjetSource | None = None
    entretien: EntretienSource
    confirmation: bool


class ConfigurationAnalyseBody(BaseModel):
    blocs: dict[str, str]


class ModificationEtape(BaseModel):
    contenu: str


def _verifier(
    confirmation: bool, contenu: str, service: ServiceValidationTranscript
) -> None:
    if not confirmation:
        raise HTTPException(status_code=422, detail="La confirmation est obligatoire.")
    validation = service.valider(contenu)
    if not validation.valide:
        raise HTTPException(
            status_code=422,
            detail={
                "raisons": [probleme._asdict() for probleme in validation.problemes]
            },
        )


def _nom_projet(nom: str) -> str:
    nom = nom.strip()
    if not nom:
        raise HTTPException(status_code=422, detail="Le nom du projet est obligatoire.")
    return nom


def _nom_est_deja_utilise(projets: list, nom: str) -> bool:
    nom_normalise = nom.strip().lower()
    return any(projet.nom.strip().lower() == nom_normalise for projet in projets)


@routeur.get("/projets")
def lister(
    produit_id: int, depot: DepotProjets = Depends(fabrique_depot_projets)
) -> list[dict]:
    return [projet._asdict() for projet in depot.lister(produit_id)]


@routeur.post("/projets", status_code=201)
def ajouter(
    body: NouveauProjet,
    depot: DepotProjets = Depends(fabrique_depot_projets),
) -> dict:
    nom = _nom_projet(body.nom)
    if _nom_est_deja_utilise(depot.lister(body.produit_id), nom):
        raise HTTPException(
            status_code=409, detail="Ce projet existe déjà pour ce produit."
        )
    try:
        return depot.ajouter(body.produit_id, nom, body.brief)._asdict()
    except ProjetDejaExistant as erreur:
        raise HTTPException(
            status_code=409, detail="Ce projet existe déjà pour ce produit."
        ) from erreur


@routeur.get("/projets/{id}")
def obtenir(id: int, depot: DepotProjets = Depends(fabrique_depot_projets)) -> dict:
    projet = depot.obtenir(id)
    if not projet:
        raise HTTPException(status_code=404)
    return projet._asdict()


@routeur.get("/projets/{id}/entretiens")
def lister_entretiens(
    id: int, depot: DepotProjets = Depends(fabrique_depot_projets)
) -> list[dict]:
    return [entretien._asdict() for entretien in depot.lister_entretiens(id)]


@routeur.get("/projets/{projet_id}/entretiens/{entretien_id}")
def obtenir_entretien(
    projet_id: int,
    entretien_id: int,
    depot: DepotProjets = Depends(fabrique_depot_projets),
) -> dict:
    entretien = depot.obtenir_entretien(projet_id, entretien_id)
    if not entretien:
        raise HTTPException(status_code=404)
    return entretien._asdict()


@routeur.post("/projets/{id}/entretiens", status_code=201)
def ajouter_entretien(
    id: int,
    body: NouvelEntretien,
    depot: DepotProjets = Depends(fabrique_depot_projets),
    validation: ServiceValidationTranscript = Depends(fabrique_service_validation),
) -> dict:
    if not depot.obtenir(id):
        raise HTTPException(status_code=404)
    _verifier(
        body.confirmation,
        body.contenu,
        validation,
    )
    return depot.ajouter_entretien(
        id,
        body.participant,
        body.date_entretien,
        body.moderateur,
        body.contenu,
        body.note_moderateur,
    )._asdict()


@routeur.post("/produits/{produit_id}/sources", status_code=201)
def ajouter_source(
    produit_id: int,
    body: NouvelleSource,
    depot: DepotProjets = Depends(fabrique_depot_projets),
    produits: DepotProduits = Depends(fabrique_depot_produits),
    validation: ServiceValidationTranscript = Depends(fabrique_service_validation),
) -> dict:
    if not any(produit.id == produit_id for produit in produits.lister()):
        raise HTTPException(status_code=404, detail="Produit introuvable.")
    if (body.projet_id is None) == (body.nouveau_projet is None):
        raise HTTPException(
            status_code=422,
            detail="Sélectionnez un projet existant ou créez un nouveau projet.",
        )
    if body.projet_id is not None:
        projet = depot.obtenir(body.projet_id)
        if not projet or projet.produit_id != produit_id:
            raise HTTPException(status_code=404, detail="Projet introuvable pour ce produit.")
        nom = None
        brief = ""
    else:
        nouveau_projet = body.nouveau_projet
        nouveau_projet = cast(NouveauProjetSource, nouveau_projet)
        nom = _nom_projet(nouveau_projet.nom)
        brief = nouveau_projet.brief
        if _nom_est_deja_utilise(depot.lister(produit_id), nom):
            raise HTTPException(
                status_code=409, detail="Ce projet existe déjà pour ce produit."
            )
    entretien = body.entretien
    _verifier(
        body.confirmation,
        entretien.contenu,
        validation,
    )
    try:
        source = depot.ajouter_source(
            produit_id,
            body.projet_id,
            nom,
            brief,
            entretien.participant,
            entretien.date_entretien,
            entretien.moderateur,
            entretien.contenu,
            entretien.note_moderateur,
        )
    except ProjetDejaExistant as erreur:
        raise HTTPException(
            status_code=409, detail="Ce projet existe déjà pour ce produit."
        ) from erreur
    return {"projet": source.projet._asdict(), "entretien": source.entretien._asdict()}


@routeur.get("/projets/{id}/scan")
def obtenir_scan(
    id: int, depot: DepotProjets = Depends(fabrique_depot_projets)
) -> dict:
    scan = depot.obtenir_scan(id)
    if not scan:
        raise HTTPException(status_code=404)
    return scan._asdict()


@routeur.post("/projets/{id}/scan", status_code=201)
def generer_scan(
    id: int, service: ServiceScansProjets = Depends(fabrique_service_scan)
) -> dict:
    try:
        return service.generer(id)._asdict()
    except ProjetIntrouvable:
        raise HTTPException(status_code=404)


@routeur.put("/projets/{id}/scan")
def modifier_scan(
    id: int, body: NouveauScan, depot: DepotProjets = Depends(fabrique_depot_projets)
) -> dict:
    scan = depot.modifier_scan(id, body.contenu)
    if not scan:
        raise HTTPException(status_code=404)
    return scan._asdict()


@routeur.post("/projets/{id}/scan/validation")
def valider_scan(
    id: int, depot: DepotProjets = Depends(fabrique_depot_projets)
) -> dict:
    scan = depot.valider_scan(id)
    if not scan:
        raise HTTPException(status_code=404)
    return scan._asdict()


def _erreur_analyse(erreur: ValueError) -> HTTPException:
    if isinstance(erreur, EtapeInaccessible):
        return HTTPException(
            status_code=409,
            detail="Validez les étapes précédentes avant de continuer.",
        )
    if isinstance(erreur, ProjetSansEntretien):
        return HTTPException(status_code=422, detail="Ajoutez au moins un entretien.")
    if isinstance(erreur, EtapeAbsente):
        return HTTPException(status_code=404, detail="Étape d’analyse introuvable.")
    return HTTPException(status_code=422, detail=str(erreur))


@routeur.get("/projets/{id}/analyse/configuration")
def obtenir_configuration_analyse(
    id: int,
    service: ServiceAnalyseProjet = Depends(fabrique_service_analyse_projet),
) -> dict:
    try:
        configuration = service.configuration(id)
    except ValueError as erreur:
        raise _erreur_analyse(erreur) from erreur
    return {
        "blocs": [bloc._asdict() for bloc in configuration.blocs],
        "etapes": [etape._asdict() for etape in configuration.etapes],
    }


@routeur.put("/projets/{id}/analyse/configuration")
def modifier_configuration_analyse(
    id: int,
    body: ConfigurationAnalyseBody,
    service: ServiceAnalyseProjet = Depends(fabrique_service_analyse_projet),
) -> dict:
    try:
        configuration = service.enregistrer_configuration(id, body.blocs)
    except ValueError as erreur:
        raise _erreur_analyse(erreur) from erreur
    return {
        "blocs": [bloc._asdict() for bloc in configuration.blocs],
        "etapes": [etape._asdict() for etape in configuration.etapes],
    }


@routeur.get("/projets/{id}/analyse/etapes")
def lister_etapes_analyse(
    id: int,
    service: ServiceAnalyseProjet = Depends(fabrique_service_analyse_projet),
) -> list[dict]:
    try:
        return [etape._asdict() for etape in service.configuration(id).etapes]
    except ValueError as erreur:
        raise _erreur_analyse(erreur) from erreur


@routeur.post("/projets/{id}/analyse/etapes/{cle}/generation", status_code=201)
def generer_etape_analyse(
    id: int,
    cle: str,
    service: ServiceAnalyseProjet = Depends(fabrique_service_analyse_projet),
) -> dict:
    try:
        return service.generer(id, cle)._asdict()
    except ValueError as erreur:
        raise _erreur_analyse(erreur) from erreur


@routeur.put("/projets/{id}/analyse/etapes/{cle}")
def modifier_etape_analyse(
    id: int,
    cle: str,
    body: ModificationEtape,
    service: ServiceAnalyseProjet = Depends(fabrique_service_analyse_projet),
) -> dict:
    try:
        return service.modifier(id, cle, body.contenu)._asdict()
    except ValueError as erreur:
        raise _erreur_analyse(erreur) from erreur


@routeur.post("/projets/{id}/analyse/etapes/{cle}/validation")
def valider_etape_analyse(
    id: int,
    cle: str,
    service: ServiceAnalyseProjet = Depends(fabrique_service_analyse_projet),
) -> dict:
    try:
        return service.valider(id, cle)._asdict()
    except ValueError as erreur:
        raise _erreur_analyse(erreur) from erreur


@routeur.get("/projets/{id}/analyse/detail")
def obtenir_detail_analyse(
    id: int,
    service: ServiceAnalyseProjet = Depends(fabrique_service_analyse_projet),
) -> dict:
    try:
        configuration = service.configuration(id)
    except ValueError as erreur:
        raise _erreur_analyse(erreur) from erreur
    return {
        "etapes": [
            {"cle": etape.cle, "libelle": etape.libelle, "contenu": etape.valide}
            for etape in configuration.etapes
            if etape.valide is not None
        ]
    }
