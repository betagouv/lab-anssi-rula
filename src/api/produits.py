from fastapi import APIRouter, Depends

from configuration import charge_configuration
from infra.postgres.depot_produits import DepotProduitsPostgres
from produits.depot import DepotProduits


def fabrique_depot_produits() -> DepotProduits:
    return DepotProduitsPostgres(charge_configuration().base_de_donnees)


routeur = APIRouter()


@routeur.get("/produits")
def lister(depot: DepotProduits = Depends(fabrique_depot_produits)) -> list[dict]:
    return [p._asdict() for p in depot.lister() if p.nom in {"MSS", "MSC"}]
