from produits.depot import DepotProduits, Produit


class DepotProduitsMemoire(DepotProduits):
    def __init__(self) -> None:
        self._produits: list[Produit] = []
        self._prochain_id = 1

    def ajouter(self, nom: str) -> Produit:
        produit = Produit(id=self._prochain_id, nom=nom)
        self._produits.append(produit)
        self._prochain_id += 1
        return produit

    def lister(self) -> list[Produit]:
        return list(self._produits)
