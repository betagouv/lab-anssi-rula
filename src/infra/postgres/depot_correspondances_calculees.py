import json
from typing import Any

from configuration import BaseDeDonnees
from correspondance.depot import Cluster, DepotCorrespondancesCalculees, Membre
from infra.connexion_base_de_donnees import avec_connexion


class DepotCorrespondancesCalculeesPostgres(DepotCorrespondancesCalculees):  # pragma: no cover
    def __init__(self, config: BaseDeDonnees) -> None:
        self._config = config
        self._connexion: Any = None

    @avec_connexion
    def sauvegarder(self, clusters: list[Cluster]) -> None:
        with self._connexion.cursor() as cur:
            cur.execute("TRUNCATE correspondances_calculees")
            if clusters:
                cur.executemany(
                    "INSERT INTO correspondances_calculees (libelle, occurrences, membres) VALUES (%s, %s, %s)",
                    [(c.libelle, c.occurrences, json.dumps([m._asdict() for m in c.membres])) for c in clusters],
                )

    @avec_connexion
    def charger(self) -> list[Cluster]:
        with self._connexion.cursor() as cur:
            cur.execute("SELECT libelle, occurrences, membres FROM correspondances_calculees ORDER BY id")
            return [Cluster(libelle=r[0], occurrences=r[1], membres=[Membre(**m) for m in r[2]]) for r in cur.fetchall()]
