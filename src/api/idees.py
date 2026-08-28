from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile

from configuration import charge_configuration
from api.imports import importer_source_csv, verifier_import
from api.produits import fabrique_depot_produits
from api.projets import fabrique_depot_projets
from idees.depot import DepotIdees
from idees.service import ServiceIdees
from projets.depot import DepotProjets
from produits.depot import DepotProduits
from infra.postgres.depot_idees import DepotIdeesPostgres
from validation_transcript.service import ServiceValidationTranscript
from api.transcripts import fabrique_service_validation_transcript

routeur = APIRouter()


def fabrique_depot_idees() -> DepotIdees:  # pragma: no cover
    return DepotIdeesPostgres(charge_configuration().base_de_donnees)


def fabrique_service_idees(
    depot: DepotIdees = Depends(fabrique_depot_idees),
) -> ServiceIdees:  # pragma: no cover
    return ServiceIdees(depot=depot)


@routeur.post("/idees/import")
def importer_csv(
    fichier: UploadFile,
    produit_id: int = Form(),
    confirmation: bool = Form(),
    service: ServiceIdees = Depends(fabrique_service_idees),
    validation: ServiceValidationTranscript = Depends(
        fabrique_service_validation_transcript
    ),
) -> list[dict]:
    try:
        contenu = fichier.file.read().decode("utf-8-sig")
        verifier_import(contenu, confirmation, validation)
        return [i._asdict() for i in service.importer(produit_id, contenu)]
    except (KeyError, ValueError) as e:
        raise HTTPException(status_code=400, detail=f"CSV invalide : {e}")


@routeur.get("/idees")
def lister_idees(
    produit_id: int | None = None,
    projet_id: int | None = None,
    service: ServiceIdees = Depends(fabrique_service_idees),
) -> list[dict]:
    return [i._asdict() for i in service.lister(produit_id, projet_id)]


@routeur.post("/produits/{produit_id}/sources/featurebase")
def importer_source_featurebase(
    produit_id: int,
    fichier: UploadFile,
    projet_id: int | None = Form(None),
    nouveau_projet_nom: str | None = Form(None),
    nouveau_projet_brief: str = Form(""),
    confirmation: bool = Form(),
    service: ServiceIdees = Depends(fabrique_service_idees),
    validation: ServiceValidationTranscript = Depends(
        fabrique_service_validation_transcript
    ),
    projets: DepotProjets = Depends(fabrique_depot_projets),
    produits: DepotProduits = Depends(fabrique_depot_produits),
) -> dict:
    contenu = fichier.file.read().decode("utf-8-sig")
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
