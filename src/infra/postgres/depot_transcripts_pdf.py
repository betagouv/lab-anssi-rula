from datetime import date
from typing import Any

from psycopg2.extras import Json

from configuration import BaseDeDonnees
from infra.connexion_base_de_donnees import avec_connexion
from transcripts_pdf.depot import DepotTranscriptsPdf, SourceTranscriptPdf

_COLONNES_SOURCE = """
    t.id, t.type_source, t.produit_id, t.nom_fichier,
    t.date_entretien, t.contenu, t.contexte, t.locuteurs, t.cree_le,
    t.termes_imposes
"""


class DepotTranscriptsPdfPostgres(DepotTranscriptsPdf):
    def __init__(self, config: BaseDeDonnees) -> None:
        self._config = config
        self._connexion: Any = None

    @avec_connexion
    def ajouter(
        self,
        type_source: str,
        produit_id: int,
        nom_source: str,
        date_entretien: date,
        contenu: str,
        contexte: str,
        locuteurs: list[dict[str, str]],
        termes_imposes: tuple[str, ...] = (),
    ) -> SourceTranscriptPdf:
        with self._connexion.cursor() as cur:
            cur.execute(
                """INSERT INTO transcripts
                   (type_source, produit_id, nom_fichier, date_entretien,
                    contenu, contexte, locuteurs, confirme, termes_imposes)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, TRUE, %s)
                   RETURNING id""",
                (
                    type_source,
                    produit_id,
                    nom_source,
                    date_entretien,
                    contenu,
                    contexte,
                    Json(locuteurs),
                    Json(list(termes_imposes)),
                ),
            )
            return self._source(cur, cur.fetchone()[0])

    @avec_connexion
    def obtenir(self, transcript_id: int) -> SourceTranscriptPdf | None:
        with self._connexion.cursor() as cur:
            cur.execute(
                f"SELECT {_COLONNES_SOURCE} FROM transcripts t "
                "WHERE t.id = %s AND t.type_source IN ('produit', 'bizdev') AND t.confirme",
                (transcript_id,),
            )
            row = cur.fetchone()
            return self._source_row(row) if row else None

    @avec_connexion
    def lister(self, produit_id: int) -> list[SourceTranscriptPdf]:
        with self._connexion.cursor() as cur:
            cur.execute(
                f"SELECT {_COLONNES_SOURCE} FROM transcripts t "
                "WHERE t.produit_id = %s AND t.produit_id IS NOT NULL "
                "AND t.type_source IN ('produit', 'bizdev') AND t.confirme "
                "ORDER BY t.cree_le DESC, t.id DESC",
                (produit_id,),
            )
            return [self._source_row(row) for row in cur.fetchall()]

    @avec_connexion
    def modifier(
        self,
        transcript_id: int,
        date_entretien: date,
        contenu: str,
        contexte: str,
        locuteurs: list[dict[str, str]],
    ) -> SourceTranscriptPdf | None:
        with self._connexion.cursor() as cur:
            cur.execute(
                """UPDATE transcripts SET date_entretien = %s, contenu = %s,
                   contexte = %s, locuteurs = %s, modifie_le = NOW()
                   WHERE id = %s AND type_source IN ('produit', 'bizdev') AND confirme
                   RETURNING id""",
                (date_entretien, contenu, contexte, Json(locuteurs), transcript_id),
            )
            row = cur.fetchone()
            return self._source(cur, row[0]) if row else None

    @avec_connexion
    def supprimer(self, transcript_id: int) -> bool:
        with self._connexion.cursor() as cur:
            cur.execute(
                "DELETE FROM transcripts WHERE id = %s AND type_source IN ('produit', 'bizdev') AND confirme RETURNING id",
                (transcript_id,),
            )
            return cur.fetchone() is not None

    @staticmethod
    def _source(cur: Any, transcript_id: int) -> SourceTranscriptPdf:
        cur.execute(
            f"SELECT {_COLONNES_SOURCE} FROM transcripts t "
            "WHERE t.id = %s AND t.type_source IN ('produit', 'bizdev') AND t.confirme",
            (transcript_id,),
        )
        return DepotTranscriptsPdfPostgres._source_row(cur.fetchone())

    @staticmethod
    def _source_row(row: tuple) -> SourceTranscriptPdf:
        return SourceTranscriptPdf(
            row[0],
            row[1],
            row[2],
            row[3],
            row[4],
            row[5],
            row[6],
            row[7],
            row[8],
            tuple(row[9]),
        )
