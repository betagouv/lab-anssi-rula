from abc import ABC, abstractmethod
from datetime import datetime
from typing import NamedTuple


class IdeeBrute(NamedTuple):
    titre: str
    nb_votes: int


class Idee(NamedTuple):
    id: int
    titre: str
    nb_votes: int
    importe_le: datetime


class DepotIdees(ABC):
    @abstractmethod
    def remplacer_toutes(self, idees: list[IdeeBrute]) -> list[Idee]: ...

    @abstractmethod
    def lister(self) -> list[Idee]: ...
