from abc import ABC, abstractmethod
from typing import Literal, NamedTuple
import unicodedata

LONGUEUR_MAXIMALE = 120
CouleurListe = Literal["blanche", "noire"]


class TermeListe(NamedTuple):
    id: int
    terme: str
    revision: int


class TermeDejaPresent(Exception): ...


class TermeAbsent(Exception): ...


class RevisionObsolete(Exception): ...


class DepotListeTermes(ABC):
    @abstractmethod
    def lister(self) -> list[TermeListe]: ...

    @abstractmethod
    def ajouter(self, terme: str, cle: str) -> TermeListe: ...

    @abstractmethod
    def modifier(
        self, identifiant: int, terme: str, cle: str, revision: int
    ) -> TermeListe: ...

    @abstractmethod
    def supprimer(self, identifiant: int, revision: int) -> None: ...


class ServiceListeTermes:
    def __init__(self, depot: DepotListeTermes) -> None:
        self._depot = depot

    def lister(self) -> list[TermeListe]:
        return self._depot.lister()

    def ajouter(self, terme: str) -> TermeListe:
        propre, cle = normaliser_terme(terme)
        return self._depot.ajouter(propre, cle)

    def modifier(self, identifiant: int, terme: str, revision: int) -> TermeListe:
        propre, cle = normaliser_terme(terme)
        return self._depot.modifier(identifiant, propre, cle, revision)

    def supprimer(self, identifiant: int, revision: int) -> None:
        self._depot.supprimer(identifiant, revision)


def normaliser_terme(terme: str) -> tuple[str, str]:
    propre = unicodedata.normalize("NFC", " ".join(terme.split()))
    if (
        not propre
        or len(propre) > LONGUEUR_MAXIMALE
        or not any(caractere.isalnum() for caractere in propre)
    ):
        raise ValueError(
            "Le terme doit contenir des lettres ou chiffres et rester court."
        )
    return propre, propre.casefold()
