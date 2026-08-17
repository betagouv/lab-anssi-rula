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


class DepotBesoinsDetectes(ABC):
    @abstractmethod
    def remplacer_source(self, source: str, besoins: list[tuple[int, str, str, str | None, int | None]]) -> list[BesoinDetecte]: ...

    @abstractmethod
    def lister(self, source: str | None = None) -> list[BesoinDetecte]: ...
