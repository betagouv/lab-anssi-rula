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
                RETURNING id, identite_id, produit_id, date_entretien, contenu, cree_le, modifie_le
                """,
                (identite_id, produit_id, date_entretien, contenu),
            )
            row = cur.fetchone()
            return Transcript(
                id=row[0], identite_id=row[1], produit_id=row[2],
                date_entretien=row[3], contenu=row[4], cree_le=row[5], modifie_le=row[6],
            )

    @avec_connexion
    def lister(self) -> list[Transcript]:
        with self._connexion.cursor() as cur:
            cur.execute(
                "SELECT id, identite_id, produit_id, date_entretien, contenu, cree_le, modifie_le FROM transcripts ORDER BY cree_le DESC"
            )
            return [
                Transcript(id=r[0], identite_id=r[1], produit_id=r[2], date_entretien=r[3], contenu=r[4], cree_le=r[5], modifie_le=r[6])
                for r in cur.fetchall()
            ]

    @avec_connexion
    def obtenir(self, id: int) -> Transcript | None:
        with self._connexion.cursor() as cur:
            cur.execute(
                "SELECT id, identite_id, produit_id, date_entretien, contenu, cree_le, modifie_le FROM transcripts WHERE id = %s",
                (id,),
            )
            row = cur.fetchone()
            if row is None:
                return None
            return Transcript(id=row[0], identite_id=row[1], produit_id=row[2], date_entretien=row[3], contenu=row[4], cree_le=row[5], modifie_le=row[6])

    @avec_connexion
    def modifier(self, id: int, identite_id: int, produit_id: int, date_entretien: date, contenu: str) -> Transcript | None:
        with self._connexion.cursor() as cur:
            cur.execute(
                """
                UPDATE transcripts
                SET identite_id = %s, produit_id = %s, date_entretien = %s, contenu = %s, modifie_le = NOW()
                WHERE id = %s
                RETURNING id, identite_id, produit_id, date_entretien, contenu, cree_le, modifie_le
                """,
                (identite_id, produit_id, date_entretien, contenu, id),
            )
            row = cur.fetchone()
            if row is None:
                return None
            return Transcript(id=row[0], identite_id=row[1], produit_id=row[2], date_entretien=row[3], contenu=row[4], cree_le=row[5], modifie_le=row[6])

    @avec_connexion
    def supprimer(self, id: int) -> bool:
        with self._connexion.cursor() as cur:
            cur.execute("DELETE FROM transcripts WHERE id = %s RETURNING id", (id,))
            return cur.fetchone() is not None
