from typing import Any

from analyses.depot import AnalyseTranscript, DepotAnalysesTranscripts
from configuration import BaseDeDonnees
from infra.connexion_base_de_donnees import avec_connexion


class DepotAnalysesTranscriptsPostgres(DepotAnalysesTranscripts):  # pragma: no cover
    def __init__(self, config: BaseDeDonnees) -> None:
        self._config = config
        self._connexion: Any = None

    @avec_connexion
    def ajouter(self, transcript_id: int, contenu: str) -> AnalyseTranscript:
        with self._connexion.cursor() as cur:
            cur.execute(
                "INSERT INTO analyses_transcripts (transcript_id, contenu) VALUES (%s, %s) RETURNING id, transcript_id, contenu, cree_le",
                (transcript_id, contenu),
            )
            row = cur.fetchone()
            return AnalyseTranscript(id=row[0], transcript_id=row[1], contenu=row[2], cree_le=row[3])

    @avec_connexion
    def obtenir_par_transcript(self, transcript_id: int) -> AnalyseTranscript | None:
        with self._connexion.cursor() as cur:
            cur.execute(
                "SELECT id, transcript_id, contenu, cree_le FROM analyses_transcripts WHERE transcript_id = %s",
                (transcript_id,),
            )
            row = cur.fetchone()
            if row is None:
                return None
            return AnalyseTranscript(id=row[0], transcript_id=row[1], contenu=row[2], cree_le=row[3])

    @avec_connexion
    def lister(self) -> list[AnalyseTranscript]:
        with self._connexion.cursor() as cur:
            cur.execute(
                "SELECT id, transcript_id, contenu, cree_le FROM analyses_transcripts ORDER BY cree_le DESC"
            )
            return [
                AnalyseTranscript(id=r[0], transcript_id=r[1], contenu=r[2], cree_le=r[3])
                for r in cur.fetchall()
            ]
