from abc import ABC, abstractmethod
from typing import NamedTuple


class Identite(NamedTuple):
    id: int
    nom: str


class DepotIdentites(ABC):
    @abstractmethod
    def ajouter(self, nom: str) -> Identite: ...

    @abstractmethod
    def lister(self) -> list[Identite]: ...
