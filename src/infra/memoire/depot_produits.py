from produits.depot import DepotProduits, Produit
from infra.memoire.depot_nomme import DepotNommeMemoire


class DepotProduitsMemoire(DepotNommeMemoire[Produit], DepotProduits):
    def __init__(self) -> None:
        super().__init__(Produit)
