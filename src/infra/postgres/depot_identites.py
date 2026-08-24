from configuration import BaseDeDonnees
from identites.depot import DepotIdentites, Identite
from infra.postgres.depot_nomme import DepotNommePostgres


class DepotIdentitesPostgres(DepotNommePostgres[Identite], DepotIdentites):  # pragma: no cover
    def __init__(self, config: BaseDeDonnees) -> None:
        super().__init__(
            config,
            Identite,
            "INSERT INTO identites (nom) VALUES (%s) RETURNING id, nom",
            "SELECT id, nom FROM identites ORDER BY nom",
        )
