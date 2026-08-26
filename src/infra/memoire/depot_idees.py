from datetime import datetime

from idees.depot import DepotIdees, Idee, IdeeBrute


class DepotIdeesMemoire(DepotIdees):
    def __init__(self) -> None:
        self._idees: list[Idee] = []
        self._prochain_id = 1

    def remplacer_toutes(self, produit_id: int, idees: list[IdeeBrute]) -> list[Idee]:
        self._idees = [i for i in self._idees if i.produit_id != produit_id]
        for brute in idees:
            self._idees.append(
                Idee(
                    id=self._prochain_id,
                    produit_id=produit_id,
                    titre=brute.titre,
                    nb_votes=brute.nb_votes,
                    importe_le=datetime.now(),
                )
            )
            self._prochain_id += 1
        return self.lister(produit_id)

    def lister(self, produit_id: int | None = None) -> list[Idee]:
        return sorted(
            (
                i
                for i in self._idees
                if produit_id is None or i.produit_id == produit_id
            ),
            key=lambda i: i.nb_votes,
            reverse=True,
        )
