from collections.abc import Callable
from typing import Any, Generic, TypeVar

from configuration import BaseDeDonnees
from infra.connexion_base_de_donnees import avec_connexion


Element = TypeVar("Element")


class DepotNommePostgres(Generic[Element]):  # pragma: no cover
    def __init__(
        self,
        config: BaseDeDonnees,
        fabrique: Callable[[int, str], Element],
        requete_ajout: str,
        requete_liste: str,
    ) -> None:
        self._config = config
        self._connexion: Any = None
        self._fabrique = fabrique
        self._requete_ajout = requete_ajout
        self._requete_liste = requete_liste

    @avec_connexion
    def ajouter(self, nom: str) -> Element:
        with self._connexion.cursor() as cur:
            cur.execute(self._requete_ajout, (nom,))
            row = cur.fetchone()
            return self._fabrique(row[0], row[1])

    @avec_connexion
    def lister(self) -> list[Element]:
        with self._connexion.cursor() as cur:
            cur.execute(self._requete_liste)
            return [self._fabrique(row[0], row[1]) for row in cur.fetchall()]
