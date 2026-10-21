from abc import ABC, abstractmethod
from typing import NamedTuple


class TermeListeBlanche(NamedTuple):
    id: int
    terme: str
    revision: int


class TermeDejaPresent(Exception): ...


class TermeAbsent(Exception): ...


class RevisionObsolete(Exception): ...


class DepotListeBlanche(ABC):
    @abstractmethod
    def lister(self) -> list[TermeListeBlanche]: ...

    @abstractmethod
    def ajouter(self, terme: str, cle: str) -> TermeListeBlanche: ...

    @abstractmethod
    def modifier(
        self, identifiant: int, terme: str, cle: str, revision: int
    ) -> TermeListeBlanche: ...

    @abstractmethod
    def supprimer(self, identifiant: int, revision: int) -> None: ...
