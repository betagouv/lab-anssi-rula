from abc import ABC, abstractmethod
from datetime import datetime
from typing import NamedTuple


class BesoinDetecte(NamedTuple):
    id: int
    source: str
    source_id: int
    texte_original: str
    nom_generique: str
    verbatim: str | None
    transcript_id: int | None
    statut: str
    cree_le: datetime
    produit_id: int | None = None


class DepotBesoinsDetectes(ABC):
    @abstractmethod
    def remplacer_source(self, source: str, besoins: list[tuple[int, str, str, str | None, int | None]], produit_id: int | None = None) -> list[BesoinDetecte]: ...

    @abstractmethod
    def lister(self, source: str | None = None, produit_id: int | None = None) -> list[BesoinDetecte]: ...

    @abstractmethod
    def restaurer(self, besoins: list[BesoinDetecte], produit_id: int) -> None: ...
