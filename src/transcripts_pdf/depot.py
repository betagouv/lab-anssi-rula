from abc import ABC, abstractmethod
from datetime import date, datetime
from typing import NamedTuple


class SourceTranscriptPdf(NamedTuple):
    id: int
    type_source: str
    produit_id: int
    projet_id: int | None
    nom_source: str
    date_entretien: date | None
    contenu: str
    contexte: str
    locuteurs: list[dict[str, str]]
    revision: int
    revision_projet: int | None
    cree_le: datetime


class JobAnalyseTranscript(NamedTuple):
    id: int
    transcript_id: int
    revision: int
    revision_projet: int | None
    statut: str
    jeton: str | None
    bail_jusqua: datetime | None


class AnalyseTranscriptPdf(NamedTuple):
    id: int
    transcript_id: int
    revision: int
    type_source: str
    contenu: dict[str, object]
    schema_version: str
    prompt_version: str
    cree_le: datetime


class DepotTranscriptsPdf(ABC):
    @abstractmethod
    def ajouter(
        self,
        type_source: str,
        produit_id: int,
        projet_id: int | None,
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

    @abstractmethod
    def obtenir_analyse(self, transcript_id: int) -> AnalyseTranscriptPdf | None: ...

    @abstractmethod
    def creer_job(
        self, transcript_id: int, relancer: bool = False
    ) -> JobAnalyseTranscript: ...

    @abstractmethod
    def obtenir_job(self, transcript_id: int) -> JobAnalyseTranscript | None: ...

    @abstractmethod
    def reclamer_job(
        self, job_id: int, duree_bail_secondes: int = 360
    ) -> JobAnalyseTranscript | None: ...

    @abstractmethod
    def finaliser(
        self,
        job: JobAnalyseTranscript,
        analyse: dict[str, object],
        fonctionnalites: list[dict[str, object]],
        schema_version: str,
        prompt_version: str,
    ) -> bool: ...

    @abstractmethod
    def echouer(self, job_id: int, jeton: str, message: str) -> None: ...

    @abstractmethod
    def lister_jobs_a_reprendre(self) -> list[int]: ...
