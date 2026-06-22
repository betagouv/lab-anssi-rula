from fastapi import APIRouter, Depends, HTTPException, UploadFile

from configuration import charge_configuration
from infra.postgres.depot_retours_bizdev import DepotRetoursBizDevPostgres
from retours_bizdev.depot import DepotRetoursBizDev
from retours_bizdev.service import ServiceRetoursBizDev

routeur = APIRouter()


def fabrique_depot_retours_bizdev() -> DepotRetoursBizDev:  # pragma: no cover
    return DepotRetoursBizDevPostgres(charge_configuration().base_de_donnees)


def fabrique_service_retours_bizdev(depot: DepotRetoursBizDev = Depends(fabrique_depot_retours_bizdev)) -> ServiceRetoursBizDev:  # pragma: no cover
    return ServiceRetoursBizDev(depot=depot)


def _decoder(raw: bytes) -> str:
    if raw.startswith(b"\xef\xbb\xbf"):
        raw = raw[3:]
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("cp1252")


@routeur.post("/retours-bizdev/import")
def importer_csv(fichier: UploadFile, service: ServiceRetoursBizDev = Depends(fabrique_service_retours_bizdev)) -> list[dict]:
    try:
        contenu = _decoder(fichier.file.read())
        return [r._asdict() for r in service.importer(contenu)]
    except (KeyError, ValueError) as e:
        raise HTTPException(status_code=400, detail=f"CSV invalide : {e}")


@routeur.get("/retours-bizdev")
def lister_retours(service: ServiceRetoursBizDev = Depends(fabrique_service_retours_bizdev)) -> list[dict]:
    return [r._asdict() for r in service.lister()]
