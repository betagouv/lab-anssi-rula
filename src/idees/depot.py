from abc import ABC, abstractmethod
from datetime import datetime
from typing import NamedTuple

from adaptateurs.featurebase import IdeeBrute


class Idee(NamedTuple):
    id: int
    id_externe: str
    titre: str
    nb_votes: int
    sync_le: datetime


class DepotIdees(ABC):
    @abstractmethod
    def upsert_toutes(self, idees: list[IdeeBrute]) -> list[Idee]: ...

    @abstractmethod
    def lister(self) -> list[Idee]: ...
