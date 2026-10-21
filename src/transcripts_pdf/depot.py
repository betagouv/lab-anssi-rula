from abc import ABC, abstractmethod
from datetime import date, datetime
from typing import NamedTuple


class SourceTranscriptPdf(NamedTuple):
    id: int
    type_source: str
    produit_id: int
    nom_source: str
    date_entretien: date | None
    contenu: str
    contexte: str
    locuteurs: list[dict[str, str]]
    cree_le: datetime


class DepotTranscriptsPdf(ABC):
    @abstractmethod
    def ajouter(
        self,
        type_source: str,
        produit_id: int,
        nom_source: str,
        date_entretien: date,
        contenu: str,
        contexte: str,
        locuteurs: list[dict[str, str]],
    ) -> SourceTranscriptPdf: ...

    @abstractmethod
    def obtenir(self, transcript_id: int) -> SourceTranscriptPdf | None: ...

    @abstractmethod
    def lister(self, produit_id: int) -> list[SourceTranscriptPdf]: ...

    @abstractmethod
    def modifier(
        self,
        transcript_id: int,
        date_entretien: date,
        contenu: str,
        contexte: str,
        locuteurs: list[dict[str, str]],
    ) -> SourceTranscriptPdf | None: ...

    @abstractmethod
    def supprimer(self, transcript_id: int) -> bool: ...
