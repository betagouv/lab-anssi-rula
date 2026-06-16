from identites.depot import DepotIdentites, Identite


class DepotIdentitesMemoire(DepotIdentites):
    def __init__(self) -> None:
        self._identites: list[Identite] = []
        self._prochain_id = 1

    def ajouter(self, nom: str) -> Identite:
        identite = Identite(id=self._prochain_id, nom=nom)
        self._identites.append(identite)
        self._prochain_id += 1
        return identite

    def lister(self) -> list[Identite]:
        return list(self._identites)
