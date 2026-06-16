from abc import ABC, abstractmethod
from typing import NamedTuple


class Produit(NamedTuple):
    id: int
    nom: str


class DepotProduits(ABC):
    @abstractmethod
    def ajouter(self, nom: str) -> Produit: ...

    @abstractmethod
    def lister(self) -> list[Produit]: ...
