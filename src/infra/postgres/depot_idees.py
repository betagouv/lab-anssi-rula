from typing import Any

from configuration import BaseDeDonnees
from idees.depot import DepotIdees, Idee, IdeeBrute
from infra.connexion_base_de_donnees import avec_connexion


class DepotIdeesPostgres(DepotIdees):  # pragma: no cover
    def __init__(self, config: BaseDeDonnees) -> None:
        self._config = config
        self._connexion: Any = None

    @avec_connexion
    def remplacer_toutes(self, idees: list[IdeeBrute]) -> list[Idee]:
        with self._connexion.cursor() as cur:
            cur.execute("TRUNCATE TABLE idees_featurebase RESTART IDENTITY")
            cur.executemany(
                "INSERT INTO idees_featurebase (titre, nb_votes) VALUES (%s, %s)",
                [(i.titre, i.nb_votes) for i in idees],
            )
        return self.lister()

    @avec_connexion
    def lister(self) -> list[Idee]:
        with self._connexion.cursor() as cur:
            cur.execute("SELECT id, titre, nb_votes, importe_le FROM idees_featurebase ORDER BY nb_votes DESC")
            return [Idee(id=r[0], titre=r[1], nb_votes=r[2], importe_le=r[3]) for r in cur.fetchall()]
