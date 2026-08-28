from datetime import datetime

from retours_bizdev.depot import DepotRetoursBizDev, Retour, RetourBrut


class DepotRetoursBizDevMemoire(DepotRetoursBizDev):
    def __init__(self) -> None:
        self._retours: list[Retour] = []
        self._prochain_id = 1

    def remplacer_tous(
        self, produit_id: int, retours: list[RetourBrut], projet_id: int | None = None
    ) -> list[Retour]:
        self._retours = [
            r
            for r in self._retours
            if not (
                r.produit_id == produit_id
                and (projet_id is None or r.projet_id == projet_id)
            )
        ]
        for brut in retours:
            self._retours.append(
                Retour(
                    id=self._prochain_id,
                    produit_id=produit_id,
                    verbatim=brut.verbatim,
                    categorie=brut.categorie,
                    item=brut.item,
                    role=brut.role,
                    qui=brut.qui,
                    date_retour=brut.date_retour,
                    importe_le=datetime.now(),
                    projet_id=projet_id,
                )
            )
            self._prochain_id += 1
        return self.lister(produit_id, projet_id)

    def lister(
        self, produit_id: int | None = None, projet_id: int | None = None
    ) -> list[Retour]:
        return [
            r
            for r in self._retours
            if (produit_id is None or r.produit_id == produit_id)
            and (projet_id is None or r.projet_id == projet_id)
        ]
