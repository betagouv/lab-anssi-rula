import json
from datetime import datetime
from typing import Any

from configuration import BaseDeDonnees
from correspondance.depot import Cluster, DepotCorrespondancesCalculees, Membre
from infra.connexion_base_de_donnees import avec_connexion


class DepotCorrespondancesCalculeesPostgres(DepotCorrespondancesCalculees):  # pragma: no cover
    def __init__(self, config: BaseDeDonnees) -> None:
        self._config = config
        self._connexion: Any = None

    @avec_connexion
    def sauvegarder(self, clusters: list[Cluster], produit_id: int | None = None) -> None:
        with self._connexion.cursor() as cur:
            cur.execute("DELETE FROM correspondances_calculees WHERE produit_id IS NOT DISTINCT FROM %s", (produit_id,))
            if clusters:
                cur.executemany(
                    "INSERT INTO correspondances_calculees (produit_id, libelle, occurrences, membres) VALUES (%s, %s, %s, %s)",
                    [(produit_id, c.libelle, c.occurrences, json.dumps([m._asdict() for m in c.membres])) for c in clusters],
                )

    @avec_connexion
    def charger(self, produit_id: int | None = None) -> list[Cluster]:
        with self._connexion.cursor() as cur:
            cur.execute("SELECT libelle, occurrences, membres FROM correspondances_calculees WHERE produit_id IS NOT DISTINCT FROM %s ORDER BY id", (produit_id,))
            return [Cluster(libelle=r[0], occurrences=r[1], membres=[Membre(**m) for m in r[2]]) for r in cur.fetchall()]

    @avec_connexion
    def dernier_calcul(self, produit_id: int | None = None) -> datetime | None:
        with self._connexion.cursor() as cur:
            cur.execute("SELECT calcule_le FROM calculs_transverses WHERE produit_id = %s", (produit_id,))
            row = cur.fetchone()
            if row:
                return row[0]
            cur.execute("SELECT MAX(calcule_le) FROM correspondances_calculees WHERE produit_id IS NOT DISTINCT FROM %s", (produit_id,))
            return cur.fetchone()[0]

    @avec_connexion
    def enregistrer_calcul(self, produit_id: int | None = None) -> None:
        if produit_id is None:
            return
        with self._connexion.cursor() as cur:
            cur.execute("INSERT INTO calculs_transverses (produit_id) VALUES (%s) ON CONFLICT (produit_id) DO UPDATE SET calcule_le = NOW()", (produit_id,))
