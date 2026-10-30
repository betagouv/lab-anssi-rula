from liste_noire.depot import DepotListeNoire, TermeListeNoire
from termes_liste import normaliser_terme


class ServiceListeNoire:
    def __init__(self, depot: DepotListeNoire) -> None:
        self._depot = depot

    def lister(self) -> list[TermeListeNoire]:
        return self._depot.lister()

    def ajouter(self, terme: str) -> TermeListeNoire:
        propre, cle = normaliser_terme(terme)
        return self._depot.ajouter(propre, cle)

    def modifier(self, identifiant: int, terme: str, revision: int) -> TermeListeNoire:
        propre, cle = normaliser_terme(terme)
        return self._depot.modifier(identifiant, propre, cle, revision)

    def supprimer(self, identifiant: int, revision: int) -> None:
        self._depot.supprimer(identifiant, revision)
