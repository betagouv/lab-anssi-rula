from threading import RLock

from termes_liste import (
    DepotListeTermes,
    RevisionObsolete,
    TermeAbsent,
    TermeDejaPresent,
    TermeListe,
)


class DepotListeTermesMemoire(DepotListeTermes):
    def __init__(self) -> None:
        self._termes: dict[int, tuple[TermeListe, str]] = {}
        self._prochain_id = 1
        self._verrou = RLock()

    def lister(self) -> list[TermeListe]:
        with self._verrou:
            return sorted(
                (terme for terme, _ in self._termes.values()),
                key=lambda terme: terme.terme.casefold(),
            )

    def ajouter(self, terme: str, cle: str) -> TermeListe:
        with self._verrou:
            if any(cle == existante for _, existante in self._termes.values()):
                raise TermeDejaPresent
            element = TermeListe(self._prochain_id, terme, 1)
            self._termes[element.id] = (element, cle)
            self._prochain_id += 1
            return element

    def modifier(self, identifiant: int, terme: str, cle: str, revision: int) -> TermeListe:
        with self._verrou:
            element = self._termes.get(identifiant)
            if element is None:
                raise TermeAbsent
            if element[0].revision != revision:
                raise RevisionObsolete
            if any(
                autre_id != identifiant and cle == existante
                for autre_id, (_, existante) in self._termes.items()
            ):
                raise TermeDejaPresent
            resultat = TermeListe(identifiant, terme, revision + 1)
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
