from configuration import BaseDeDonnees
from infra.postgres.depot_nomme import DepotNommePostgres
from produits.depot import DepotProduits, Produit


class DepotProduitsPostgres(DepotNommePostgres[Produit], DepotProduits):  # pragma: no cover
    def __init__(self, config: BaseDeDonnees) -> None:
        super().__init__(
            config,
            Produit,
            "INSERT INTO produits (nom) VALUES (%s) RETURNING id, nom",
            "SELECT id, nom FROM produits ORDER BY nom",
        )
