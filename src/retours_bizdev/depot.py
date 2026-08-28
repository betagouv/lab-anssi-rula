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
    produit_id: int
    verbatim: str
    categorie: str | None
    item: str | None
    role: str | None
    qui: str | None
    date_retour: str | None
    importe_le: datetime
    projet_id: int | None = None


class DepotRetoursBizDev(ABC):
    @abstractmethod
    def remplacer_tous(
        self, produit_id: int, retours: list[RetourBrut], projet_id: int | None = None
    ) -> list[Retour]: ...

    @abstractmethod
    def lister(
        self, produit_id: int | None = None, projet_id: int | None = None
    ) -> list[Retour]: ...
