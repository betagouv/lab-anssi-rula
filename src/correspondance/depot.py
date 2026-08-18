from abc import ABC, abstractmethod
from typing import NamedTuple

Cle = tuple[str, int]


class Feature(NamedTuple):
    source: str
    id: int
    texte: str
    transcript_id: int | None
    verbatim: str | None


class Membre(NamedTuple):
    source: str
    texte: str
    transcript_id: int | None
    verbatim: str | None
    source_id: int | None = None


class Cluster(NamedTuple):
    libelle: str
    occurrences: int
    membres: list[Membre]


class DepotCorrespondance(ABC):
    @abstractmethod
    def features_sans_embedding(self) -> list[Feature]: ...

    @abstractmethod
    def enregistrer_embeddings(self, items: list[tuple[str, int, list[float]]]) -> None: ...

    @abstractmethod
    def lister_features(self) -> list[Feature]: ...

    @abstractmethod
    def paires_proches(self, seuil: float) -> list[tuple[Cle, Cle]]: ...


class DepotCorrespondancesCalculees(ABC):
    @abstractmethod
    def sauvegarder(self, clusters: list[Cluster]) -> None: ...

    @abstractmethod
    def charger(self) -> list[Cluster]: ...
