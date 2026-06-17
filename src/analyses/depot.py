from abc import ABC, abstractmethod
from datetime import datetime
from typing import NamedTuple


class AnalyseTranscript(NamedTuple):
    id: int
    transcript_id: int
    contenu: str
    cree_le: datetime


class DepotAnalysesTranscripts(ABC):
    @abstractmethod
    def ajouter(self, transcript_id: int, contenu: str) -> AnalyseTranscript: ...

    @abstractmethod
    def obtenir_par_transcript(self, transcript_id: int) -> AnalyseTranscript | None: ...

    @abstractmethod
    def lister(self) -> list[AnalyseTranscript]: ...
