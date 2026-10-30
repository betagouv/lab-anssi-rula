from typing import Any

import psycopg2

from configuration import BaseDeDonnees
from infra.connexion_base_de_donnees import avec_connexion
from termes_liste import (
    CouleurListe,
    DepotListeTermes,
    RevisionObsolete,
    TermeAbsent,
    TermeDejaPresent,
    TermeListe,
)

_TABLES: dict[CouleurListe, str] = {
    "blanche": "termes_liste_blanche",
    "noire": "termes_liste_noire",
}


class DepotListeTermesPostgres(DepotListeTermes):
    def __init__(self, config: BaseDeDonnees, couleur: CouleurListe) -> None:
        self._config = config
        self._connexion: Any = None
        self._table = _TABLES[couleur]

    @avec_connexion
    def lister(self) -> list[TermeListe]:
        with self._connexion.cursor() as cur:
            cur.execute(f"SELECT id, terme, revision FROM {self._table} ORDER BY terme_normalise")
            return [TermeListe(*row) for row in cur.fetchall()]

    @avec_connexion
    def ajouter(self, terme: str, cle: str) -> TermeListe:
        with self._connexion.cursor() as cur:
            try:
                cur.execute(
                    f"INSERT INTO {self._table} (terme, terme_normalise) VALUES (%s, %s) RETURNING id, terme, revision",
                    (terme, cle),
                )
            except psycopg2.errors.UniqueViolation as erreur:
                raise TermeDejaPresent from erreur
            return TermeListe(*cur.fetchone())

    @avec_connexion
    def modifier(self, identifiant: int, terme: str, cle: str, revision: int) -> TermeListe:
        with self._connexion.cursor() as cur:
            try:
                cur.execute(
                    f"UPDATE {self._table} SET terme = %s, terme_normalise = %s, revision = revision + 1 WHERE id = %s AND revision = %s RETURNING id, terme, revision",
                    (terme, cle, identifiant, revision),
                )
            except psycopg2.errors.UniqueViolation as erreur:
                raise TermeDejaPresent from erreur
            row = cur.fetchone()
            if row:
                return TermeListe(*row)
            cur.execute(f"SELECT 1 FROM {self._table} WHERE id = %s", (identifiant,))
            if cur.fetchone() is None:
                raise TermeAbsent
            raise RevisionObsolete

    @avec_connexion
    def supprimer(self, identifiant: int, revision: int) -> None:
        with self._connexion.cursor() as cur:
            cur.execute(
                f"DELETE FROM {self._table} WHERE id = %s AND revision = %s",
                (identifiant, revision),
            )
            if cur.rowcount:
                return
            cur.execute(f"SELECT 1 FROM {self._table} WHERE id = %s", (identifiant,))
            if cur.fetchone() is None:
                raise TermeAbsent
            raise RevisionObsolete
