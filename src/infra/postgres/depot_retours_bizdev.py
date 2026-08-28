from typing import Any

from configuration import BaseDeDonnees
from infra.connexion_base_de_donnees import avec_connexion
from retours_bizdev.depot import DepotRetoursBizDev, Retour, RetourBrut


class DepotRetoursBizDevPostgres(DepotRetoursBizDev):  # pragma: no cover
    def __init__(self, config: BaseDeDonnees) -> None:
        self._config = config
        self._connexion: Any = None

    @avec_connexion
    def remplacer_tous(
        self, produit_id: int, retours: list[RetourBrut], projet_id: int | None = None
    ) -> list[Retour]:
        with self._connexion.cursor() as cur:
            if projet_id is None:
                cur.execute(
                    "DELETE FROM retours_bizdev WHERE produit_id = %s", (produit_id,)
                )
            else:
                cur.execute(
                    "DELETE FROM retours_bizdev WHERE produit_id = %s AND projet_id = %s",
                    (produit_id, projet_id),
                )
            cur.executemany(
                "INSERT INTO retours_bizdev (produit_id, projet_id, verbatim, categorie, item, role, qui, date_retour) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                [
                    (
                        produit_id,
                        projet_id,
                        r.verbatim,
                        r.categorie,
                        r.item,
                        r.role,
                        r.qui,
                        r.date_retour,
                    )
                    for r in retours
                ],
            )
        self._connexion.commit()
        return self.lister(produit_id, projet_id)

    @avec_connexion
    def lister(
        self, produit_id: int | None = None, projet_id: int | None = None
    ) -> list[Retour]:
        with self._connexion.cursor() as cur:
            cur.execute(
                "SELECT id, produit_id, verbatim, categorie, item, role, qui, date_retour, importe_le, projet_id FROM retours_bizdev WHERE produit_id = COALESCE(%s, produit_id) AND (%s IS NULL OR projet_id = %s) ORDER BY importe_le DESC",
                (produit_id, projet_id, projet_id),
            )
            return [
                Retour(
                    id=r[0],
                    produit_id=r[1],
                    verbatim=r[2],
                    categorie=r[3],
                    item=r[4],
                    role=r[5],
                    qui=r[6],
                    date_retour=r[7],
                    importe_le=r[8],
                    projet_id=r[9],
                )
                for r in cur.fetchall()
            ]
