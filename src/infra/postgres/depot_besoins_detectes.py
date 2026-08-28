from typing import Any

from besoins.depot import BesoinDetecte, DepotBesoinsDetectes
from configuration import BaseDeDonnees
from infra.connexion_base_de_donnees import avec_connexion


class DepotBesoinsDetectesPostgres(DepotBesoinsDetectes):  # pragma: no cover
    def __init__(self, config: BaseDeDonnees) -> None:
        self._config = config
        self._connexion: Any = None

    @avec_connexion
    def remplacer_source(self, source: str, besoins: list[tuple[int, str, str, str | None, int | None]], produit_id: int | None = None) -> list[BesoinDetecte]:
        with self._connexion.cursor() as cur:
            cur.execute(
                "DELETE FROM besoins_detectes WHERE source = %s AND (%s IS NULL OR produit_id = %s)",
                (source, produit_id, produit_id),
            )
            cur.executemany(
                """INSERT INTO besoins_detectes
                   (source, source_id, texte_original, nom_generique, verbatim, transcript_id, statut, produit_id)
                   VALUES (%s, %s, %s, %s, %s, %s, 'extrait', %s)""",
                [(source, source_id, texte, nom, verbatim, transcript_id, produit_id) for source_id, texte, nom, verbatim, transcript_id in besoins],
            )
        self._connexion.commit()
        return self.lister(source, produit_id)

    @avec_connexion
    def lister(self, source: str | None = None, produit_id: int | None = None) -> list[BesoinDetecte]:
        with self._connexion.cursor() as cur:
            if source is None:
                cur.execute(
                    """SELECT id, source, source_id, texte_original, nom_generique,
                              verbatim, transcript_id, statut, cree_le, produit_id,
                              CASE WHEN b.source = 'transcript' THEN
                                (SELECT t.projet_id FROM transcripts t WHERE t.id = b.transcript_id)
                              END AS projet_id
                       FROM besoins_detectes b
                       WHERE (%s IS NULL OR b.produit_id = %s)
                       ORDER BY source, id""",
                    (produit_id, produit_id),
                )
            else:
                cur.execute(
                    """SELECT id, source, source_id, texte_original, nom_generique,
                              verbatim, transcript_id, statut, cree_le, produit_id,
                              CASE WHEN b.source = 'transcript' THEN
                                (SELECT t.projet_id FROM transcripts t WHERE t.id = b.transcript_id)
                              END AS projet_id
                       FROM besoins_detectes b
                       WHERE b.source = %s AND (%s IS NULL OR b.produit_id = %s)
                       ORDER BY id""",
                    (source, produit_id, produit_id),
                )
            return [BesoinDetecte(*r) for r in cur.fetchall()]

    @avec_connexion
    def restaurer(self, besoins: list[BesoinDetecte], produit_id: int) -> None:
        with self._connexion.cursor() as cur:
            cur.execute("DELETE FROM besoins_detectes WHERE produit_id = %s", (produit_id,))
            cur.executemany(
                """INSERT INTO besoins_detectes
                   (id, source, source_id, texte_original, nom_generique, verbatim, transcript_id, statut, cree_le, produit_id)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                [(b.id, b.source, b.source_id, b.texte_original, b.nom_generique, b.verbatim, b.transcript_id, b.statut, b.cree_le, b.produit_id) for b in besoins],
            )
            cur.execute("SELECT setval('besoins_detectes_id_seq', COALESCE(MAX(id), 1), MAX(id) IS NOT NULL) FROM besoins_detectes")
