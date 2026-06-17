from fastapi import APIRouter, Depends, HTTPException

from adaptateurs.featurebase import AdaptateurFeatureBaseReel
from configuration import charge_configuration
from idees.depot import DepotIdees
from idees.service import ServiceIdees
from infra.postgres.depot_idees import DepotIdeesPostgres

routeur = APIRouter()


def fabrique_depot_idees() -> DepotIdees:  # pragma: no cover
    return DepotIdeesPostgres(charge_configuration().base_de_donnees)


def fabrique_service_idees(depot: DepotIdees = Depends(fabrique_depot_idees)) -> ServiceIdees:  # pragma: no cover
    return ServiceIdees(depot=depot, featurebase=AdaptateurFeatureBaseReel(charge_configuration().featurebase))


@routeur.post("/idees/sync")
def synchroniser(service: ServiceIdees = Depends(fabrique_service_idees)) -> list[dict]:
    try:
        return [i._asdict() for i in service.synchroniser()]
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))


@routeur.get("/idees")
def lister_idees(service: ServiceIdees = Depends(fabrique_service_idees)) -> list[dict]:
    return [i._asdict() for i in service.lister()]
