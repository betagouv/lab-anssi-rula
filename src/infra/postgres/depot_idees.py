from typing import Any

from configuration import BaseDeDonnees
from idees.depot import DepotIdees, Idee, IdeeBrute
from infra.connexion_base_de_donnees import avec_connexion


class DepotIdeesPostgres(DepotIdees):  # pragma: no cover
    def __init__(self, config: BaseDeDonnees) -> None:
        self._config = config
        self._connexion: Any = None

    @avec_connexion
    def remplacer_toutes(
        self, produit_id: int, idees: list[IdeeBrute], projet_id: int | None = None
    ) -> list[Idee]:
        with self._connexion.cursor() as cur:
            if projet_id is None:
                cur.execute(
                    "DELETE FROM idees_featurebase WHERE produit_id = %s", (produit_id,)
                )
            else:
                cur.execute(
                    "DELETE FROM idees_featurebase WHERE produit_id = %s AND projet_id = %s",
                    (produit_id, projet_id),
                )
            cur.executemany(
                "INSERT INTO idees_featurebase (produit_id, projet_id, titre, nb_votes) VALUES (%s, %s, %s, %s)",
                [(produit_id, projet_id, i.titre, i.nb_votes) for i in idees],
            )
        return self.lister(produit_id, projet_id)

    @avec_connexion
    def lister(
        self, produit_id: int | None = None, projet_id: int | None = None
    ) -> list[Idee]:
        with self._connexion.cursor() as cur:
            cur.execute(
                "SELECT id, produit_id, titre, nb_votes, importe_le, projet_id FROM idees_featurebase WHERE produit_id = COALESCE(%s, produit_id) AND (%s IS NULL OR projet_id = %s) ORDER BY nb_votes DESC",
                (produit_id, projet_id, projet_id),
            )
            return [
                Idee(
                    id=r[0],
                    produit_id=r[1],
                    titre=r[2],
                    nb_votes=r[3],
                    importe_le=r[4],
                    projet_id=r[5],
                )
                for r in cur.fetchall()
            ]
