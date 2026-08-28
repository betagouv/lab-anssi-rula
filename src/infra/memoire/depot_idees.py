from datetime import datetime

from idees.depot import DepotIdees, Idee, IdeeBrute


class DepotIdeesMemoire(DepotIdees):
    def __init__(self) -> None:
        self._idees: list[Idee] = []
        self._prochain_id = 1

    def remplacer_toutes(
        self, produit_id: int, idees: list[IdeeBrute], projet_id: int | None = None
    ) -> list[Idee]:
        self._idees = [
            i
            for i in self._idees
            if not (
                i.produit_id == produit_id
                and (projet_id is None or i.projet_id == projet_id)
            )
        ]
        for brute in idees:
            self._idees.append(
                Idee(
                    id=self._prochain_id,
                    produit_id=produit_id,
                    titre=brute.titre,
                    nb_votes=brute.nb_votes,
                    importe_le=datetime.now(),
                    projet_id=projet_id,
                )
            )
            self._prochain_id += 1
        return self.lister(produit_id, projet_id)

    def lister(
        self, produit_id: int | None = None, projet_id: int | None = None
    ) -> list[Idee]:
        return sorted(
            (
                i
                for i in self._idees
                if (produit_id is None or i.produit_id == produit_id)
                and (projet_id is None or i.projet_id == projet_id)
            ),
            key=lambda i: i.nb_votes,
            reverse=True,
        )
