from liste_blanche.depot import DepotListeBlanche, TermeListeBlanche
from termes_liste import normaliser_terme


class ServiceListeBlanche:
    def __init__(self, depot: DepotListeBlanche) -> None:
        self._depot = depot

    def lister(self) -> list[TermeListeBlanche]:
        return self._depot.lister()

    def ajouter(self, terme: str) -> TermeListeBlanche:
        propre, cle = normaliser_terme(terme)
        return self._depot.ajouter(propre, cle)

    def modifier(
        self, identifiant: int, terme: str, revision: int
    ) -> TermeListeBlanche:
        propre, cle = normaliser_terme(terme)
        return self._depot.modifier(identifiant, propre, cle, revision)

    def supprimer(self, identifiant: int, revision: int) -> None:
        self._depot.supprimer(identifiant, revision)
