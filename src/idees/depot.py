from abc import ABC, abstractmethod
from datetime import datetime
from typing import NamedTuple


class IdeeBrute(NamedTuple):
    titre: str
    nb_votes: int


class Idee(NamedTuple):
    id: int
    produit_id: int
    titre: str
    nb_votes: int
    importe_le: datetime
    projet_id: int | None = None


class DepotIdees(ABC):
    @abstractmethod
    def remplacer_toutes(
        self, produit_id: int, idees: list[IdeeBrute], projet_id: int | None = None
    ) -> list[Idee]: ...

    @abstractmethod
    def lister(
        self, produit_id: int | None = None, projet_id: int | None = None
    ) -> list[Idee]: ...
