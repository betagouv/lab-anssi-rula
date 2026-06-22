from datetime import datetime

from retours_bizdev.depot import DepotRetoursBizDev, Retour, RetourBrut


class DepotRetoursBizDevMemoire(DepotRetoursBizDev):
    def __init__(self) -> None:
        self._retours: list[Retour] = []
        self._prochain_id = 1

    def remplacer_tous(self, retours: list[RetourBrut]) -> list[Retour]:
        self._retours = []
        self._prochain_id = 1
        for brut in retours:
            self._retours.append(
                Retour(
                    id=self._prochain_id,
                    verbatim=brut.verbatim,
                    categorie=brut.categorie,
                    item=brut.item,
                    role=brut.role,
                    qui=brut.qui,
                    date_retour=brut.date_retour,
                    importe_le=datetime.now(),
                )
            )
            self._prochain_id += 1
        return self.lister()

    def lister(self) -> list[Retour]:
        return list(self._retours)
