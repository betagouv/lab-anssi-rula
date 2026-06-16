from typing import Any

from configuration import BaseDeDonnees
from infra.connexion_base_de_donnees import avec_connexion
from produits.depot import DepotProduits, Produit


class DepotProduitsPostgres(DepotProduits):  # pragma: no cover
    def __init__(self, config: BaseDeDonnees) -> None:
        self._config = config
        self._connexion: Any = None

    @avec_connexion
    def ajouter(self, nom: str) -> Produit:
        with self._connexion.cursor() as cur:
            cur.execute("INSERT INTO produits (nom) VALUES (%s) RETURNING id, nom", (nom,))
            row = cur.fetchone()
            return Produit(id=row[0], nom=row[1])

    @avec_connexion
    def lister(self) -> list[Produit]:
        with self._connexion.cursor() as cur:
            cur.execute("SELECT id, nom FROM produits ORDER BY nom")
            return [Produit(id=r[0], nom=r[1]) for r in cur.fetchall()]
