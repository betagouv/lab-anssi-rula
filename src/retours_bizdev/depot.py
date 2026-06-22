from abc import ABC, abstractmethod
from datetime import datetime
from typing import NamedTuple


class RetourBrut(NamedTuple):
    verbatim: str
    categorie: str | None
    item: str | None
    role: str | None
    qui: str | None
    date_retour: str | None


class Retour(NamedTuple):
    id: int
    verbatim: str
    categorie: str | None
    item: str | None
    role: str | None
    qui: str | None
    date_retour: str | None
    importe_le: datetime


class DepotRetoursBizDev(ABC):
    @abstractmethod
    def remplacer_tous(self, retours: list[RetourBrut]) -> list[Retour]: ...

    @abstractmethod
    def lister(self) -> list[Retour]: ...
