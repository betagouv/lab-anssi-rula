from typing import Any

import psycopg2

from configuration import BaseDeDonnees
from infra.connexion_base_de_donnees import avec_connexion
from liste_noire.depot import (
    DepotListeNoire,
    RevisionObsolete,
    TermeAbsent,
    TermeDejaPresent,
    TermeListeNoire,
)


class DepotListeNoirePostgres(DepotListeNoire):
    def __init__(self, config: BaseDeDonnees) -> None:
        self._config = config
        self._connexion: Any = None

    @avec_connexion
    def lister(self) -> list[TermeListeNoire]:
        with self._connexion.cursor() as cur:
            cur.execute(
                "SELECT id, terme, revision FROM termes_liste_noire "
                "ORDER BY terme_normalise"
            )
            return [TermeListeNoire(*row) for row in cur.fetchall()]

    @avec_connexion
    def ajouter(self, terme: str, cle: str) -> TermeListeNoire:
        with self._connexion.cursor() as cur:
            try:
                cur.execute(
                    "INSERT INTO termes_liste_noire (terme, terme_normalise) "
                    "VALUES (%s, %s) RETURNING id, terme, revision",
                    (terme, cle),
                )
            except psycopg2.errors.UniqueViolation as erreur:
                raise TermeDejaPresent from erreur
            return TermeListeNoire(*cur.fetchone())

    @avec_connexion
    def modifier(
        self, identifiant: int, terme: str, cle: str, revision: int
    ) -> TermeListeNoire:
        with self._connexion.cursor() as cur:
            try:
                cur.execute(
                    "UPDATE termes_liste_noire SET terme = %s, terme_normalise = %s, "
                    "revision = revision + 1 WHERE id = %s AND revision = %s "
                    "RETURNING id, terme, revision",
                    (terme, cle, identifiant, revision),
                )
            except psycopg2.errors.UniqueViolation as erreur:
                raise TermeDejaPresent from erreur
            row = cur.fetchone()
            if row:
                return TermeListeNoire(*row)
            cur.execute(
                "SELECT 1 FROM termes_liste_noire WHERE id = %s", (identifiant,)
            )
            if cur.fetchone() is None:
                raise TermeAbsent
            raise RevisionObsolete

    @avec_connexion
    def supprimer(self, identifiant: int, revision: int) -> None:
        with self._connexion.cursor() as cur:
            cur.execute(
                "DELETE FROM termes_liste_noire WHERE id = %s AND revision = %s",
                (identifiant, revision),
            )
            if cur.rowcount:
                return
            cur.execute(
                "SELECT 1 FROM termes_liste_noire WHERE id = %s", (identifiant,)
            )
            if cur.fetchone() is None:
                raise TermeAbsent
            raise RevisionObsolete
