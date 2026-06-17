from typing import Any

from configuration import BaseDeDonnees
from fonctionnalites.depot import DepotFonctionnalitesTranscripts, Fonctionnalite
from infra.connexion_base_de_donnees import avec_connexion


class DepotFonctionnalitesTranscriptsPostgres(DepotFonctionnalitesTranscripts):  # pragma: no cover
    def __init__(self, config: BaseDeDonnees) -> None:
        self._config = config
        self._connexion: Any = None

    @avec_connexion
    def ajouter_toutes(self, transcript_id: int, contenus: list[str]) -> list[Fonctionnalite]:
        with self._connexion.cursor() as cur:
            cur.executemany(
                "INSERT INTO fonctionnalites_transcripts (transcript_id, contenu) VALUES (%s, %s)",
                [(transcript_id, c) for c in contenus],
            )
        return self.obtenir_par_transcript(transcript_id)

    @avec_connexion
    def obtenir_par_transcript(self, transcript_id: int) -> list[Fonctionnalite]:
        with self._connexion.cursor() as cur:
            cur.execute(
                "SELECT id, transcript_id, contenu, cree_le FROM fonctionnalites_transcripts WHERE transcript_id = %s ORDER BY id",
                (transcript_id,),
            )
            return [Fonctionnalite(id=r[0], transcript_id=r[1], contenu=r[2], cree_le=r[3]) for r in cur.fetchall()]

    @avec_connexion
    def lister(self) -> list[Fonctionnalite]:
        with self._connexion.cursor() as cur:
            cur.execute("SELECT id, transcript_id, contenu, cree_le FROM fonctionnalites_transcripts ORDER BY transcript_id, id")
            return [Fonctionnalite(id=r[0], transcript_id=r[1], contenu=r[2], cree_le=r[3]) for r in cur.fetchall()]
