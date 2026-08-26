from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile

from configuration import charge_configuration
from api.imports import verifier_import
from idees.depot import DepotIdees
from idees.service import ServiceIdees
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
    service: ServiceIdees = Depends(fabrique_service_idees),
) -> list[dict]:
    return [i._asdict() for i in service.lister(produit_id)]
