from threading import RLock

from liste_noire.depot import (
    DepotListeNoire,
    RevisionObsolete,
    TermeAbsent,
    TermeDejaPresent,
    TermeListeNoire,
)


class DepotListeNoireMemoire(DepotListeNoire):
    def __init__(self) -> None:
        self._termes: dict[int, tuple[TermeListeNoire, str]] = {}
        self._prochain_id = 1
        self._verrou = RLock()

    def lister(self) -> list[TermeListeNoire]:
        with self._verrou:
            return sorted(
                (terme for terme, _ in self._termes.values()),
                key=lambda terme: terme.terme.casefold(),
            )

    def ajouter(self, terme: str, cle: str) -> TermeListeNoire:
        with self._verrou:
            if any(cle == existante for _, existante in self._termes.values()):
                raise TermeDejaPresent
            element = TermeListeNoire(self._prochain_id, terme, 1)
            self._termes[element.id] = (element, cle)
            self._prochain_id += 1
            return element

    def modifier(
        self, identifiant: int, terme: str, cle: str, revision: int
    ) -> TermeListeNoire:
        with self._verrou:
            element = self._termes.get(identifiant)
            if element is None:
                raise TermeAbsent
            if element[0].revision != revision:
                raise RevisionObsolete
            if any(
                existant_id != identifiant and cle == existante
                for existant_id, (_, existante) in self._termes.items()
            ):
                raise TermeDejaPresent
            resultat = TermeListeNoire(identifiant, terme, revision + 1)
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
