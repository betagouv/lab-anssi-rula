from adaptateurs.featurebase import AdaptateurFeatureBase, IdeeBrute


class AdaptateurFeatureBaseDeTest(AdaptateurFeatureBase):
    def __init__(self) -> None:
        self._idees: list[IdeeBrute] = []

    def avec_idees(self, idees: list[IdeeBrute]) -> "AdaptateurFeatureBaseDeTest":
        self._idees = idees
        return self

    def lister_idees(self) -> list[IdeeBrute]:
        return list(self._idees)
