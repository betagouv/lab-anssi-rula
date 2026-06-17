from datetime import datetime

from adaptateurs.featurebase import IdeeBrute
from idees.depot import DepotIdees, Idee


class DepotIdeesMemoire(DepotIdees):
    def __init__(self) -> None:
        self._idees: dict[str, Idee] = {}
        self._prochain_id = 1

    def upsert_toutes(self, idees: list[IdeeBrute]) -> list[Idee]:
        for brute in idees:
            existante = self._idees.get(brute.id_externe)
            id_ = existante.id if existante else self._prochain_id
            if not existante:
                self._prochain_id += 1
            self._idees[brute.id_externe] = Idee(
                id=id_, id_externe=brute.id_externe, titre=brute.titre, nb_votes=brute.nb_votes, sync_le=datetime.now()
            )
        return self.lister()

    def lister(self) -> list[Idee]:
        return sorted(self._idees.values(), key=lambda i: i.nb_votes, reverse=True)
