from datetime import datetime

from correspondance.depot import Cluster, DepotCorrespondancesCalculees


class DepotCorrespondancesCalculeesMemoire(DepotCorrespondancesCalculees):
    def __init__(self) -> None:
        self._clusters: dict[int | None, list[Cluster]] = {}
        self._dates: dict[int | None, datetime] = {}

    def sauvegarder(self, clusters: list[Cluster], produit_id: int | None = None) -> None:
        self._clusters[produit_id] = list(clusters)
        self._dates[produit_id] = datetime.now()

    def charger(self, produit_id: int | None = None) -> list[Cluster]:
        return list(self._clusters.get(produit_id, []))

    def dernier_calcul(self, produit_id: int | None = None) -> datetime | None:
        return self._dates.get(produit_id)

    def enregistrer_calcul(self, produit_id: int | None = None) -> None:
        if produit_id is not None:
            self._dates[produit_id] = datetime.now()
