from collections.abc import Callable
from typing import Generic, TypeVar


Element = TypeVar("Element")


class DepotNommeMemoire(Generic[Element]):
    def __init__(self, fabrique: Callable[[int, str], Element]) -> None:
        self._elements: list[Element] = []
        self._prochain_id = 1
        self._fabrique = fabrique

    def ajouter(self, nom: str) -> Element:
        element = self._fabrique(self._prochain_id, nom)
        self._elements.append(element)
        self._prochain_id += 1
        return element

    def lister(self) -> list[Element]:
        return list(self._elements)
