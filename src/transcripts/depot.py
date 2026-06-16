from abc import ABC, abstractmethod
from datetime import date, datetime
from typing import NamedTuple


class Transcript(NamedTuple):
    id: int
    identite_id: int
    produit_id: int
    date_entretien: date
    contenu: str
    cree_le: datetime
    modifie_le: datetime


class DepotTranscripts(ABC):
    @abstractmethod
    def ajouter(self, identite_id: int, produit_id: int, date_entretien: date, contenu: str) -> Transcript: ...

    @abstractmethod
    def lister(self) -> list[Transcript]: ...

    @abstractmethod
    def obtenir(self, id: int) -> Transcript | None: ...

    @abstractmethod
    def modifier(self, id: int, identite_id: int, produit_id: int, date_entretien: date, contenu: str) -> Transcript | None: ...

    @abstractmethod
    def supprimer(self, id: int) -> bool: ...
