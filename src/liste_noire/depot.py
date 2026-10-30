from abc import ABC, abstractmethod
from typing import NamedTuple


class TermeListeNoire(NamedTuple):
    id: int
    terme: str
    revision: int


class TermeDejaPresent(Exception): ...


class TermeAbsent(Exception): ...


class RevisionObsolete(Exception): ...


class DepotListeNoire(ABC):
    @abstractmethod
    def lister(self) -> list[TermeListeNoire]: ...

    @abstractmethod
    def ajouter(self, terme: str, cle: str) -> TermeListeNoire: ...

    @abstractmethod
    def modifier(
        self, identifiant: int, terme: str, cle: str, revision: int
    ) -> TermeListeNoire: ...

    @abstractmethod
    def supprimer(self, identifiant: int, revision: int) -> None: ...
