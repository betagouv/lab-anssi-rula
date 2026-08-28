from abc import ABC, abstractmethod
from datetime import date, datetime
from typing import NamedTuple


class Projet(NamedTuple):
    id: int
    produit_id: int
    nom: str
    brief: str
    cree_le: datetime


class Entretien(NamedTuple):
    id: int
    projet_id: int
    participant: str
    date_entretien: date
    moderateur: str
    contenu: str
    note_moderateur: str
    cree_le: datetime


class ScanProjet(NamedTuple):
    projet_id: int
    brouillon: str
    valide: str | None
    cree_le: datetime
    modifie_le: datetime


class SourceProjet(NamedTuple):
    projet: Projet
    entretien: Entretien


class DepotProjets(ABC):
    @abstractmethod
    def ajouter(self, produit_id: int, nom: str, brief: str) -> Projet: ...

    @abstractmethod
    def lister(self, produit_id: int) -> list[Projet]: ...

    @abstractmethod
    def obtenir(self, id: int) -> Projet | None: ...

    @abstractmethod
    def supprimer(self, id: int) -> bool: ...

    @abstractmethod
    def ajouter_entretien(
        self,
        projet_id: int,
        participant: str,
        date_entretien: date,
        moderateur: str,
        contenu: str,
        note_moderateur: str,
    ) -> Entretien: ...

    @abstractmethod
    def ajouter_source(
        self,
        produit_id: int,
        projet_id: int | None,
        nom: str | None,
        brief: str,
        participant: str,
        date_entretien: date,
        moderateur: str,
        contenu: str,
        note_moderateur: str,
    ) -> SourceProjet: ...

    @abstractmethod
    def lister_entretiens(self, projet_id: int) -> list[Entretien]: ...

    @abstractmethod
    def enregistrer_scan(self, projet_id: int, brouillon: str) -> ScanProjet: ...

    @abstractmethod
    def obtenir_scan(self, projet_id: int) -> ScanProjet | None: ...

    @abstractmethod
    def modifier_scan(self, projet_id: int, brouillon: str) -> ScanProjet | None: ...

    @abstractmethod
    def valider_scan(self, projet_id: int) -> ScanProjet | None: ...
