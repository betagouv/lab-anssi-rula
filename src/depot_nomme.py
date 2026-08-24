from abc import ABC, abstractmethod
from typing import Generic, TypeVar


Element = TypeVar("Element")


class DepotNomme(ABC, Generic[Element]):
    @abstractmethod
    def ajouter(self, nom: str) -> Element: ...

    @abstractmethod
    def lister(self) -> list[Element]: ...
