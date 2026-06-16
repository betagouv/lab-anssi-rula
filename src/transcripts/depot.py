from abc import ABC, abstractmethod
from datetime import date
from typing import NamedTuple


class Transcript(NamedTuple):
    id: int
    identite_id: int
    produit_id: int
    date_entretien: date
    contenu: str


class DepotTranscripts(ABC):
    @abstractmethod
    def ajouter(self, identite_id: int, produit_id: int, date_entretien: date, contenu: str) -> Transcript: ...

    @abstractmethod
    def lister(self) -> list[Transcript]: ...
