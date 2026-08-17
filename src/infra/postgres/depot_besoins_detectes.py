from typing import Any

from besoins.depot import BesoinDetecte, DepotBesoinsDetectes
from configuration import BaseDeDonnees
from infra.connexion_base_de_donnees import avec_connexion


class DepotBesoinsDetectesPostgres(DepotBesoinsDetectes):  # pragma: no cover
    def __init__(self, config: BaseDeDonnees) -> None:
        self._config = config
        self._connexion: Any = None

    @avec_connexion
    def remplacer_source(self, source: str, besoins: list[tuple[int, str, str, str | None, int | None]]) -> list[BesoinDetecte]:
        with self._connexion.cursor() as cur:
            cur.execute("DELETE FROM besoins_detectes WHERE source = %s", (source,))
            cur.executemany(
                """INSERT INTO besoins_detectes
                   (source, source_id, texte_original, nom_generique, verbatim, transcript_id, statut)
                   VALUES (%s, %s, %s, %s, %s, %s, 'extrait')""",
                [(source, source_id, texte, nom, verbatim, transcript_id) for source_id, texte, nom, verbatim, transcript_id in besoins],
            )
        return self.lister(source)

    @avec_connexion
    def lister(self, source: str | None = None) -> list[BesoinDetecte]:
        with self._connexion.cursor() as cur:
            if source is None:
                cur.execute(
                    """SELECT id, source, source_id, texte_original, nom_generique,
                              verbatim, transcript_id, statut, cree_le
                       FROM besoins_detectes ORDER BY source, id"""
                )
            else:
                cur.execute(
                    """SELECT id, source, source_id, texte_original, nom_generique,
                              verbatim, transcript_id, statut, cree_le
                       FROM besoins_detectes WHERE source = %s ORDER BY id""",
                    (source,),
                )
            return [BesoinDetecte(*r) for r in cur.fetchall()]
