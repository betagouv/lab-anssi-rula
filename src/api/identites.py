from fastapi import APIRouter, Depends
from pydantic import BaseModel

from configuration import charge_configuration
from identites.depot import DepotIdentites
from infra.postgres.depot_identites import DepotIdentitesPostgres


def fabrique_depot_identites() -> DepotIdentites:  # pragma: no cover
    return DepotIdentitesPostgres(charge_configuration().base_de_donnees)


class NouvelleIdentite(BaseModel):
    nom: str


routeur = APIRouter()


@routeur.get("/identites")
def lister(depot: DepotIdentites = Depends(fabrique_depot_identites)) -> list[dict]:
    return [i._asdict() for i in depot.lister()]


@routeur.post("/identites", status_code=201)
def ajouter(body: NouvelleIdentite, depot: DepotIdentites = Depends(fabrique_depot_identites)) -> dict:
    return depot.ajouter(body.nom)._asdict()
