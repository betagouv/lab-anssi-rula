from typing import NamedTuple

from depot_nomme import DepotNomme


class Produit(NamedTuple):
    id: int
    nom: str


class DepotProduits(DepotNomme[Produit]):
    pass
