from typing import Any

from configuration import BaseDeDonnees
from identites.depot import DepotIdentites, Identite
from infra.connexion_base_de_donnees import avec_connexion


class DepotIdentitesPostgres(DepotIdentites):  # pragma: no cover
    def __init__(self, config: BaseDeDonnees) -> None:
        self._config = config
        self._connexion: Any = None

    @avec_connexion
    def ajouter(self, nom: str) -> Identite:
        with self._connexion.cursor() as cur:
            cur.execute("INSERT INTO identites (nom) VALUES (%s) RETURNING id, nom", (nom,))
            row = cur.fetchone()
            return Identite(id=row[0], nom=row[1])

    @avec_connexion
    def lister(self) -> list[Identite]:
        with self._connexion.cursor() as cur:
            cur.execute("SELECT id, nom FROM identites ORDER BY nom")
            return [Identite(id=r[0], nom=r[1]) for r in cur.fetchall()]
