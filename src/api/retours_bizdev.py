from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile

from configuration import charge_configuration
from api.imports import verifier_import
from infra.postgres.depot_retours_bizdev import DepotRetoursBizDevPostgres
from retours_bizdev.depot import DepotRetoursBizDev
from retours_bizdev.service import ServiceRetoursBizDev
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
    service: ServiceRetoursBizDev = Depends(fabrique_service_retours_bizdev),
) -> list[dict]:
    return [r._asdict() for r in service.lister(produit_id)]
