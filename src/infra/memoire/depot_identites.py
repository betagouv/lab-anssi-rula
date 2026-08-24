from identites.depot import DepotIdentites, Identite
from infra.memoire.depot_nomme import DepotNommeMemoire


class DepotIdentitesMemoire(DepotNommeMemoire[Identite], DepotIdentites):
    def __init__(self) -> None:
        super().__init__(Identite)
