from correspondance.depot import Cluster, DepotCorrespondancesCalculees


class DepotCorrespondancesCalculeesMemoire(DepotCorrespondancesCalculees):
    def __init__(self) -> None:
        self._clusters: list[Cluster] = []

    def sauvegarder(self, clusters: list[Cluster]) -> None:
        self._clusters = list(clusters)

    def charger(self) -> list[Cluster]:
        return list(self._clusters)
