from datetime import date
from typing import Any

from psycopg2.extras import Json

from configuration import BaseDeDonnees
from infra.connexion_base_de_donnees import avec_connexion
from transcripts_pdf.depot import (
    AnalyseTranscriptPdf,
    DepotTranscriptsPdf,
    JobAnalyseTranscript,
    SourceTranscriptPdf,
)

_COLONNES_SOURCE = """
    t.id, t.type_source, t.produit_id, t.projet_id, t.nom_fichier,
    t.date_entretien, t.contenu, t.contexte, t.locuteurs, t.revision_corpus,
    p.revision_corpus, t.cree_le
"""


class DepotTranscriptsPdfPostgres(DepotTranscriptsPdf):  # pragma: no cover
    def __init__(self, config: BaseDeDonnees) -> None:
        self._config = config
        self._connexion: Any = None

    @avec_connexion
    def ajouter(
        self,
        type_source: str,
        produit_id: int,
        projet_id: int | None,
        nom_source: str,
        date_entretien: date,
        contenu: str,
        contexte: str,
        locuteurs: list[dict[str, str]],
    ) -> SourceTranscriptPdf:
        with self._connexion.cursor() as cur:
            cur.execute(
                """INSERT INTO transcripts
                   (type_source, produit_id, projet_id, titre, nom_fichier,
                    date_entretien, contenu, contexte, locuteurs, participant,
                    confirme)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, TRUE)
                   RETURNING id""",
                (
                    type_source,
                    produit_id,
                    projet_id,
                    nom_source,
                    nom_source,
                    date_entretien,
                    contenu,
                    contexte,
                    Json(locuteurs),
                    "Transcript PDF",
                ),
            )
            return self._source(cur, cur.fetchone()[0])

    @avec_connexion
    def obtenir(self, transcript_id: int) -> SourceTranscriptPdf | None:
        with self._connexion.cursor() as cur:
            cur.execute(
                f"SELECT {_COLONNES_SOURCE} FROM transcripts t "
                "LEFT JOIN projets_recherche p ON p.id = t.projet_id "
                "WHERE t.id = %s AND t.type_source IN ('produit', 'bizdev') AND t.confirme",
                (transcript_id,),
            )
            row = cur.fetchone()
            return SourceTranscriptPdf(*row) if row else None

    @avec_connexion
    def lister(self, produit_id: int) -> list[SourceTranscriptPdf]:
        with self._connexion.cursor() as cur:
            cur.execute(
                f"SELECT {_COLONNES_SOURCE} FROM transcripts t "
                "LEFT JOIN projets_recherche p ON p.id = t.projet_id "
                "WHERE t.produit_id = %s AND t.type_source IN ('produit', 'bizdev') "
                "AND t.confirme ORDER BY t.cree_le DESC, t.id DESC",
                (produit_id,),
            )
            return [SourceTranscriptPdf(*row) for row in cur.fetchall()]

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
                   contexte = %s, locuteurs = %s, revision_corpus = revision_corpus + 1,
                   modifie_le = NOW()
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
                "DELETE FROM transcripts WHERE id = %s AND type_source IN ('produit', 'bizdev') RETURNING id",
                (transcript_id,),
            )
            return cur.fetchone() is not None

    @avec_connexion
    def obtenir_analyse(self, transcript_id: int) -> AnalyseTranscriptPdf | None:
        with self._connexion.cursor() as cur:
            cur.execute(
                """SELECT id, transcript_id, revision, type_source, contenu,
                          schema_version, prompt_version, cree_le
                   FROM analyses_transcripts_pdf WHERE transcript_id = %s
                   ORDER BY revision DESC LIMIT 1""",
                (transcript_id,),
            )
            row = cur.fetchone()
            return AnalyseTranscriptPdf(*row) if row else None

    @avec_connexion
    def creer_job(
        self, transcript_id: int, relancer: bool = False
    ) -> JobAnalyseTranscript:
        with self._connexion.cursor() as cur:
            cur.execute(
                """INSERT INTO jobs_analyse_transcripts
                   (transcript_id, revision, revision_projet)
                   SELECT t.id, t.revision_corpus, p.revision_corpus
                   FROM transcripts t LEFT JOIN projets_recherche p ON p.id = t.projet_id
                   WHERE t.id = %s AND t.type_source IN ('produit', 'bizdev') AND t.confirme
                   ON CONFLICT (transcript_id, revision) DO NOTHING""",
                (transcript_id,),
            )
            if relancer:
                cur.execute(
                    """UPDATE jobs_analyse_transcripts j
                       SET statut = 'attente', revision_projet = p.revision_corpus,
                           erreur = NULL, modifie_le = NOW()
                       FROM transcripts t LEFT JOIN projets_recherche p ON p.id = t.projet_id
                       WHERE j.transcript_id = %s AND j.transcript_id = t.id
                         AND j.revision = t.revision_corpus AND j.statut = 'echec'
                       RETURNING j.id, j.transcript_id, j.revision, j.revision_projet,
                                 j.statut, j.jeton, j.bail_jusqua""",
                    (transcript_id,),
                )
                row = cur.fetchone()
                if row:
                    return JobAnalyseTranscript(*row)
            cur.execute(
                """SELECT id, transcript_id, revision, revision_projet, statut,
                          jeton, bail_jusqua FROM jobs_analyse_transcripts
                   WHERE transcript_id = %s ORDER BY revision DESC LIMIT 1""",
                (transcript_id,),
            )
            row = cur.fetchone()
            if row is None:
                raise ValueError("Transcript confirmé introuvable.")
            return JobAnalyseTranscript(*row)

    @avec_connexion
    def reclamer_job(
        self, job_id: int, duree_bail_secondes: int = 360
    ) -> JobAnalyseTranscript | None:
        with self._connexion.cursor() as cur:
            cur.execute(
                """UPDATE jobs_analyse_transcripts
                   SET statut = 'en_cours', jeton = gen_random_uuid(),
                       bail_jusqua = NOW() + (%s * INTERVAL '1 second'),
                       tentatives = tentatives + 1, modifie_le = NOW()
                   WHERE id = %s AND (statut = 'attente' OR
                       (statut = 'en_cours' AND bail_jusqua < NOW()))
                   RETURNING id, transcript_id, revision, revision_projet, statut,
                             jeton::text, bail_jusqua""",
                (duree_bail_secondes, job_id),
            )
            row = cur.fetchone()
            return JobAnalyseTranscript(*row) if row else None

    @avec_connexion
    def obtenir_job(self, transcript_id: int) -> JobAnalyseTranscript | None:
        with self._connexion.cursor() as cur:
            cur.execute(
                """SELECT id, transcript_id, revision, revision_projet, statut,
                          jeton::text, bail_jusqua
                   FROM jobs_analyse_transcripts WHERE transcript_id = %s
                   ORDER BY revision DESC LIMIT 1""",
                (transcript_id,),
            )
            row = cur.fetchone()
            return JobAnalyseTranscript(*row) if row else None

    @avec_connexion
    def finaliser(
        self,
        job: JobAnalyseTranscript,
        analyse: dict[str, object],
        fonctionnalites: list[dict[str, object]],
        schema_version: str,
        prompt_version: str,
    ) -> bool:
        if job.jeton is None:
            return False
        with self._connexion.cursor() as cur:
            cur.execute(
                """SELECT type_source, produit_id, projet_id, revision_corpus
                   FROM transcripts WHERE id = %s AND confirme FOR UPDATE""",
                (job.transcript_id,),
            )
            source = cur.fetchone()
            if source is None or source[3] != job.revision:
                return False
            type_source, produit_id, projet_id = source[:3]
            revision_projet = None
            if projet_id is not None:
                cur.execute(
                    "SELECT revision_corpus FROM projets_recherche WHERE id = %s FOR UPDATE",
                    (projet_id,),
                )
                projet = cur.fetchone()
                if projet is None:
                    return False
                revision_projet = projet[0]
            if revision_projet != job.revision_projet:
                return False
            cur.execute(
                """SELECT id FROM jobs_analyse_transcripts
                   WHERE id = %s AND transcript_id = %s AND revision = %s
                     AND revision_projet IS NOT DISTINCT FROM %s
                     AND jeton = %s AND statut = 'en_cours' FOR UPDATE""",
                (
                    job.id,
                    job.transcript_id,
                    job.revision,
                    job.revision_projet,
                    job.jeton,
                ),
            )
            if cur.fetchone() is None:
                return False
            cur.execute(
                """INSERT INTO analyses_transcripts_pdf
                   (transcript_id, revision, type_source, contenu, schema_version, prompt_version)
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (
                    job.transcript_id,
                    job.revision,
                    type_source,
                    Json(analyse),
                    schema_version,
                    prompt_version,
                ),
            )
            source = f"transcript_{type_source}"
            cur.executemany(
                """WITH fonctionnalite AS (
                       INSERT INTO fonctionnalites_transcripts
                           (transcript_id, contenu, verbatim)
                       VALUES (%s, %s, %s) RETURNING id, contenu, verbatim
                   )
                   INSERT INTO besoins_detectes
                       (source, source_id, texte_original, nom_generique, verbatim,
                        transcript_id, produit_id)
                   SELECT %s, id, contenu, contenu, verbatim, %s, %s
                   FROM fonctionnalite""",
                [
                    (
                        job.transcript_id,
                        item["action"],
                        item["verbatim"],
                        source,
                        job.transcript_id,
                        produit_id,
                    )
                    for item in fonctionnalites
                ],
            )
            cur.execute(
                """UPDATE jobs_analyse_transcripts
                   SET statut = 'termine', jeton = NULL, bail_jusqua = NULL,
                       erreur = NULL, modifie_le = NOW()
                   WHERE id = %s AND jeton = %s""",
                (job.id, job.jeton),
            )
            return cur.rowcount == 1

    @avec_connexion
    def echouer(self, job_id: int, jeton: str, message: str) -> None:
        with self._connexion.cursor() as cur:
            cur.execute(
                """UPDATE jobs_analyse_transcripts
                   SET statut = 'echec', jeton = NULL, bail_jusqua = NULL,
                       erreur = %s, modifie_le = NOW()
                   WHERE id = %s AND jeton = %s AND statut = 'en_cours'""",
                (message, job_id, jeton),
            )

    @avec_connexion
    def lister_jobs_a_reprendre(self) -> list[int]:
        with self._connexion.cursor() as cur:
            cur.execute(
                """SELECT id FROM jobs_analyse_transcripts
                   WHERE statut = 'attente' OR
                       (statut = 'en_cours' AND bail_jusqua < NOW())
                   ORDER BY id"""
            )
            return [row[0] for row in cur.fetchall()]

    @staticmethod
    def _source(cur: Any, transcript_id: int) -> SourceTranscriptPdf:
        cur.execute(
            f"SELECT {_COLONNES_SOURCE} FROM transcripts t "
            "LEFT JOIN projets_recherche p ON p.id = t.projet_id WHERE t.id = %s",
            (transcript_id,),
        )
        return SourceTranscriptPdf(*cur.fetchone())
