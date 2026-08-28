from abc import ABC, abstractmethod
from datetime import datetime
from typing import NamedTuple

Cle = tuple[str, int]


class Feature(NamedTuple):
    source: str
    id: int
    texte: str
    transcript_id: int | None
    verbatim: str | None
    produit_id: int | None = None


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
    def features_sans_embedding(self, produit_id: int | None = None) -> list[Feature]: ...

    @abstractmethod
    def enregistrer_embeddings(self, items: list[tuple[str, int, list[float]]]) -> None: ...

    @abstractmethod
    def lister_features(self, produit_id: int | None = None) -> list[Feature]: ...

    @abstractmethod
    def paires_proches(self, seuil: float, produit_id: int | None = None) -> list[tuple[Cle, Cle]]: ...


class DepotCorrespondancesCalculees(ABC):
    @abstractmethod
    def sauvegarder(self, clusters: list[Cluster], produit_id: int | None = None) -> None: ...

    @abstractmethod
    def charger(self, produit_id: int | None = None) -> list[Cluster]: ...

    @abstractmethod
    def dernier_calcul(self, produit_id: int | None = None) -> datetime | None: ...

    @abstractmethod
    def enregistrer_calcul(self, produit_id: int | None = None) -> None: ...
