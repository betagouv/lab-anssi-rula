from abc import ABC, abstractmethod
from datetime import datetime
from typing import NamedTuple


class Fonctionnalite(NamedTuple):
    id: int
    transcript_id: int
    contenu: str
    verbatim: str | None
    cree_le: datetime


class DepotFonctionnalitesTranscripts(ABC):
    @abstractmethod
    def ajouter_toutes(self, transcript_id: int, items: list[tuple[str, str | None]]) -> list[Fonctionnalite]: ...

    @abstractmethod
    def obtenir_par_transcript(self, transcript_id: int) -> list[Fonctionnalite]: ...

    @abstractmethod
    def lister(self) -> list[Fonctionnalite]: ...
