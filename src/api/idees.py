from fastapi import APIRouter, Depends, HTTPException, UploadFile

from configuration import charge_configuration
from idees.depot import DepotIdees
from idees.service import ServiceIdees
from infra.postgres.depot_idees import DepotIdeesPostgres

routeur = APIRouter()


def fabrique_depot_idees() -> DepotIdees:  # pragma: no cover
    return DepotIdeesPostgres(charge_configuration().base_de_donnees)


def fabrique_service_idees(depot: DepotIdees = Depends(fabrique_depot_idees)) -> ServiceIdees:  # pragma: no cover
    return ServiceIdees(depot=depot)


@routeur.post("/idees/import")
def importer_csv(fichier: UploadFile, service: ServiceIdees = Depends(fabrique_service_idees)) -> list[dict]:
    try:
        contenu = fichier.file.read().decode("utf-8-sig")
        return [i._asdict() for i in service.importer(contenu)]
    except (KeyError, ValueError) as e:
        raise HTTPException(status_code=400, detail=f"CSV invalide : {e}")


@routeur.get("/idees")
def lister_idees(service: ServiceIdees = Depends(fabrique_service_idees)) -> list[dict]:
    return [i._asdict() for i in service.lister()]
