from threading import RLock

from liste_blanche.depot import (
    DepotListeBlanche,
    RevisionObsolete,
    TermeAbsent,
    TermeDejaPresent,
    TermeListeBlanche,
)


class DepotListeBlancheMemoire(DepotListeBlanche):
    def __init__(self) -> None:
        self._termes: dict[int, tuple[TermeListeBlanche, str]] = {}
        self._prochain_id = 1
        self._verrou = RLock()

    def lister(self) -> list[TermeListeBlanche]:
        with self._verrou:
            return sorted(
                (terme for terme, _ in self._termes.values()),
                key=lambda terme: terme.terme.casefold(),
            )

    def ajouter(self, terme: str, cle: str) -> TermeListeBlanche:
        with self._verrou:
            if any(cle == cle_existante for _, cle_existante in self._termes.values()):
                raise TermeDejaPresent
            element = TermeListeBlanche(self._prochain_id, terme, 1)
            self._termes[element.id] = (element, cle)
            self._prochain_id += 1
            return element

    def modifier(
        self, identifiant: int, terme: str, cle: str, revision: int
    ) -> TermeListeBlanche:
        with self._verrou:
            element = self._termes.get(identifiant)
            if element is None:
                raise TermeAbsent
            if element[0].revision != revision:
                raise RevisionObsolete
            if any(
                identifiant_existant != identifiant and cle == cle_existante
                for identifiant_existant, (_, cle_existante) in self._termes.items()
            ):
                raise TermeDejaPresent
            resultat = TermeListeBlanche(identifiant, terme, revision + 1)
            self._termes[identifiant] = (resultat, cle)
            return resultat

    def supprimer(self, identifiant: int, revision: int) -> None:
        with self._verrou:
            element = self._termes.get(identifiant)
            if element is None:
                raise TermeAbsent
            if element[0].revision != revision:
                raise RevisionObsolete
            del self._termes[identifiant]
