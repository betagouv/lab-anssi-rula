from typing import NamedTuple

from depot_nomme import DepotNomme


class Identite(NamedTuple):
    id: int
    nom: str


class DepotIdentites(DepotNomme[Identite]):
    pass
