from adaptateurs.featurebase import AdaptateurFeatureBase
from idees.depot import DepotIdees, Idee


class ServiceIdees:
    def __init__(self, depot: DepotIdees, featurebase: AdaptateurFeatureBase) -> None:
        self._depot = depot
        self._featurebase = featurebase

    def synchroniser(self) -> list[Idee]:
        return self._depot.upsert_toutes(self._featurebase.lister_idees())

    def lister(self) -> list[Idee]:
        return self._depot.lister()
