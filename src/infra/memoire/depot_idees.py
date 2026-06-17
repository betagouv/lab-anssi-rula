from datetime import datetime

from idees.depot import DepotIdees, Idee, IdeeBrute


class DepotIdeesMemoire(DepotIdees):
    def __init__(self) -> None:
        self._idees: list[Idee] = []
        self._prochain_id = 1

    def remplacer_toutes(self, idees: list[IdeeBrute]) -> list[Idee]:
        self._idees = []
        self._prochain_id = 1
        for brute in idees:
            self._idees.append(Idee(id=self._prochain_id, titre=brute.titre, nb_votes=brute.nb_votes, importe_le=datetime.now()))
            self._prochain_id += 1
        return self.lister()

    def lister(self) -> list[Idee]:
        return sorted(self._idees, key=lambda i: i.nb_votes, reverse=True)
