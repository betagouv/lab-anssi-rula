from datetime import date
from typing import Any

from configuration import BaseDeDonnees
from infra.connexion_base_de_donnees import avec_connexion
from transcripts.depot import DepotTranscripts, Transcript


class DepotTranscriptsPostgres(DepotTranscripts):  # pragma: no cover
    def __init__(self, config: BaseDeDonnees) -> None:
        self._config = config
        self._connexion: Any = None

    @avec_connexion
    def ajouter(self, identite_id: int, produit_id: int, date_entretien: date, contenu: str) -> Transcript:
        with self._connexion.cursor() as cur:
            cur.execute(
                """
                INSERT INTO transcripts (identite_id, produit_id, date_entretien, contenu)
                VALUES (%s, %s, %s, %s)
                RETURNING id, identite_id, produit_id, date_entretien, contenu
                """,
                (identite_id, produit_id, date_entretien, contenu),
            )
            row = cur.fetchone()
            return Transcript(
                id=row[0], identite_id=row[1], produit_id=row[2],
                date_entretien=row[3], contenu=row[4],
            )

    @avec_connexion
    def lister(self) -> list[Transcript]:
        with self._connexion.cursor() as cur:
            cur.execute(
                "SELECT id, identite_id, produit_id, date_entretien, contenu FROM transcripts ORDER BY cree_le DESC"
            )
            return [Transcript(id=r[0], identite_id=r[1], produit_id=r[2], date_entretien=r[3], contenu=r[4]) for r in cur.fetchall()]
