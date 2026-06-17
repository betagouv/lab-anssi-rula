from typing import Any

from configuration import BaseDeDonnees
from adaptateurs.featurebase import IdeeBrute
from idees.depot import DepotIdees, Idee
from infra.connexion_base_de_donnees import avec_connexion


class DepotIdeesPostgres(DepotIdees):  # pragma: no cover
    def __init__(self, config: BaseDeDonnees) -> None:
        self._config = config
        self._connexion: Any = None

    @avec_connexion
    def upsert_toutes(self, idees: list[IdeeBrute]) -> list[Idee]:
        with self._connexion.cursor() as cur:
            cur.executemany(
                """INSERT INTO idees_featurebase (id_externe, titre, nb_votes, sync_le)
                   VALUES (%s, %s, %s, NOW())
                   ON CONFLICT (id_externe) DO UPDATE
                   SET titre = EXCLUDED.titre, nb_votes = EXCLUDED.nb_votes, sync_le = EXCLUDED.sync_le""",
                [(i.id_externe, i.titre, i.nb_votes) for i in idees],
            )
        return self.lister()

    @avec_connexion
    def lister(self) -> list[Idee]:
        with self._connexion.cursor() as cur:
            cur.execute("SELECT id, id_externe, titre, nb_votes, sync_le FROM idees_featurebase ORDER BY nb_votes DESC")
            return [Idee(id=r[0], id_externe=r[1], titre=r[2], nb_votes=r[3], sync_le=r[4]) for r in cur.fetchall()]
