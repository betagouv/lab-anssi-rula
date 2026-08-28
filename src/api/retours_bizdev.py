from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile

from configuration import charge_configuration
from api.imports import importer_source_csv, verifier_import
from api.produits import fabrique_depot_produits
from api.projets import fabrique_depot_projets
from infra.postgres.depot_retours_bizdev import DepotRetoursBizDevPostgres
from retours_bizdev.depot import DepotRetoursBizDev
from retours_bizdev.service import ServiceRetoursBizDev
from projets.depot import DepotProjets
from produits.depot import DepotProduits
from validation_transcript.service import ServiceValidationTranscript
from api.transcripts import fabrique_service_validation_transcript

routeur = APIRouter()


def fabrique_depot_retours_bizdev() -> DepotRetoursBizDev:  # pragma: no cover
    return DepotRetoursBizDevPostgres(charge_configuration().base_de_donnees)


def fabrique_service_retours_bizdev(
    depot: DepotRetoursBizDev = Depends(fabrique_depot_retours_bizdev),
) -> ServiceRetoursBizDev:  # pragma: no cover
    return ServiceRetoursBizDev(depot=depot)


def _decoder(raw: bytes) -> str:
    if raw.startswith(b"\xef\xbb\xbf"):
        raw = raw[3:]
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("cp1252")


@routeur.post("/retours-bizdev/import")
def importer_csv(
    fichier: UploadFile,
    produit_id: int = Form(),
    confirmation: bool = Form(),
    service: ServiceRetoursBizDev = Depends(fabrique_service_retours_bizdev),
    validation: ServiceValidationTranscript = Depends(
        fabrique_service_validation_transcript
    ),
) -> list[dict]:
    try:
        contenu = _decoder(fichier.file.read())
        verifier_import(contenu, confirmation, validation)
        return [r._asdict() for r in service.importer(produit_id, contenu)]
    except (KeyError, ValueError) as e:
        raise HTTPException(status_code=400, detail=f"CSV invalide : {e}")


@routeur.get("/retours-bizdev")
def lister_retours(
    produit_id: int | None = None,
    projet_id: int | None = None,
    service: ServiceRetoursBizDev = Depends(fabrique_service_retours_bizdev),
) -> list[dict]:
    return [r._asdict() for r in service.lister(produit_id, projet_id)]


@routeur.post("/produits/{produit_id}/sources/bizdev")
def importer_source_bizdev(
    produit_id: int,
    fichier: UploadFile,
    projet_id: int | None = Form(None),
    nouveau_projet_nom: str | None = Form(None),
    nouveau_projet_brief: str = Form(""),
    confirmation: bool = Form(),
    service: ServiceRetoursBizDev = Depends(fabrique_service_retours_bizdev),
    validation: ServiceValidationTranscript = Depends(
        fabrique_service_validation_transcript
    ),
    projets: DepotProjets = Depends(fabrique_depot_projets),
    produits: DepotProduits = Depends(fabrique_depot_produits),
) -> dict:
    contenu = _decoder(fichier.file.read())
    return importer_source_csv(
        produit_id,
        contenu,
        confirmation,
        projet_id,
        nouveau_projet_nom,
        nouveau_projet_brief,
        validation,
        projets,
        produits,
        service.importer,
    )
