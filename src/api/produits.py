from fastapi import APIRouter, Depends
from pydantic import BaseModel

from configuration import charge_configuration
from infra.postgres.depot_produits import DepotProduitsPostgres
from produits.depot import DepotProduits


def fabrique_depot_produits() -> DepotProduits:  # pragma: no cover
    return DepotProduitsPostgres(charge_configuration().base_de_donnees)


class NouveauProduit(BaseModel):
    nom: str


routeur = APIRouter()


@routeur.get("/produits")
def lister(depot: DepotProduits = Depends(fabrique_depot_produits)) -> list[dict]:
    return [p._asdict() for p in depot.lister()]


@routeur.post("/produits", status_code=201)
def ajouter(body: NouveauProduit, depot: DepotProduits = Depends(fabrique_depot_produits)) -> dict:
    return depot.ajouter(body.nom)._asdict()
