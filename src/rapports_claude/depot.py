from abc import ABC, abstractmethod
from datetime import datetime
from typing import NamedTuple
from uuid import UUID


class TranscriptCatalogueClaude(NamedTuple):
    id: int
    type_source: str
    produit_id: int
    projet_id: int | None
    revision: int
    nombre_rapports: int
    analyse_courante: bool
    cree_le: datetime


class SourceTranscriptClaude(NamedTuple):
    id: int
    type_source: str
    produit_id: int
    projet_id: int | None
    revision: int
    confirme: bool
    contenu: str
    contexte: str
    locuteurs: list[dict[str, str]]
    cree_le: datetime


class RapportClaudeMetadonnees(NamedTuple):
    id: int
    transcript_id: int
    revision: int
    cree_le: datetime
    courant: bool


class RapportClaude(NamedTuple):
    id: int
    transcript_id: int
    revision: int
    empreinte: str
    cree_le: datetime
    courant: bool
    contenu: str
    cle_idempotence: UUID


class DepotRapportsClaude(ABC):
    @abstractmethod
    def lister_transcripts(
        self,
        produit_id: int | None,
        projet_id: int | None,
        type_source: str | None,
        statut: str,
        limite: int,
        curseur: int | None,
    ) -> tuple[list[TranscriptCatalogueClaude], int | None]: ...

    @abstractmethod
    def obtenir_source(self, transcript_id: int) -> SourceTranscriptClaude | None: ...

    @abstractmethod
    def lister_rapports(
        self, transcript_id: int, limite: int, curseur: int | None
    ) -> tuple[list[RapportClaudeMetadonnees], int | None]: ...

    @abstractmethod
    def obtenir_rapport(self, rapport_id: int) -> RapportClaude | None: ...

    @abstractmethod
    def enregistrer(
        self,
        transcript_id: int,
        revision: int,
        empreinte: str,
        cle_idempotence: UUID,
        contenu: str,
    ) -> RapportClaude: ...


class SourceIntrouvable(Exception):
    pass


class RapportIntrouvable(Exception):
    pass


class SourceNonEligible(Exception):
    pass


class SourceModifiee(Exception):
    pass


class ConflitIdempotence(Exception):
    pass


class EntreeInvalide(Exception):
    pass
