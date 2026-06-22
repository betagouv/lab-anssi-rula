from typing import Any

from configuration import BaseDeDonnees
from infra.connexion_base_de_donnees import avec_connexion
from retours_bizdev.depot import DepotRetoursBizDev, Retour, RetourBrut


class DepotRetoursBizDevPostgres(DepotRetoursBizDev):  # pragma: no cover
    def __init__(self, config: BaseDeDonnees) -> None:
        self._config = config
        self._connexion: Any = None

    @avec_connexion
    def remplacer_tous(self, retours: list[RetourBrut]) -> list[Retour]:
        with self._connexion.cursor() as cur:
            cur.execute("TRUNCATE TABLE retours_bizdev RESTART IDENTITY")
            cur.executemany(
                "INSERT INTO retours_bizdev (verbatim, categorie, item, role, qui, date_retour) VALUES (%s, %s, %s, %s, %s, %s)",
                [(r.verbatim, r.categorie, r.item, r.role, r.qui, r.date_retour) for r in retours],
            )
        return self.lister()

    @avec_connexion
    def lister(self) -> list[Retour]:
        with self._connexion.cursor() as cur:
            cur.execute(
                "SELECT id, verbatim, categorie, item, role, qui, date_retour, importe_le FROM retours_bizdev ORDER BY importe_le DESC"
            )
            return [Retour(id=r[0], verbatim=r[1], categorie=r[2], item=r[3], role=r[4], qui=r[5], date_retour=r[6], importe_le=r[7]) for r in cur.fetchall()]
