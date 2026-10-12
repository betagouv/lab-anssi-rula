from datetime import date, datetime, timedelta
from uuid import uuid4

from transcripts_pdf.depot import (
    AnalyseTranscriptPdf,
    DepotTranscriptsPdf,
    JobAnalyseTranscript,
    SourceTranscriptPdf,
)


class DepotTranscriptsPdfMemoire(DepotTranscriptsPdf):
    def __init__(self) -> None:
        self.sources: list[SourceTranscriptPdf] = []
        self.jobs: list[JobAnalyseTranscript] = []
        self.analyses: list[AnalyseTranscriptPdf] = []
        self.fonctionnalites: list[dict[str, object]] = []
        self._prochain_id = 1
        self._prochain_job = 1

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
        maintenant = datetime.now()
        source = SourceTranscriptPdf(
            self._prochain_id,
            type_source,
            produit_id,
            projet_id,
            nom_source,
            date_entretien,
            contenu,
            contexte,
            locuteurs,
            1,
            1 if projet_id else None,
            maintenant,
        )
        self.sources.append(source)
        self._prochain_id += 1
        return source

    def obtenir(self, transcript_id: int) -> SourceTranscriptPdf | None:
        return next(
            (source for source in self.sources if source.id == transcript_id), None
        )

    def lister(self, produit_id: int) -> list[SourceTranscriptPdf]:
        return [source for source in self.sources if source.produit_id == produit_id]

    def modifier(
        self,
        transcript_id: int,
        date_entretien: date,
        contenu: str,
        contexte: str,
        locuteurs: list[dict[str, str]],
    ) -> SourceTranscriptPdf | None:
        source = self.obtenir(transcript_id)
        if source is None:
            return None
        modifiee = source._replace(
            date_entretien=date_entretien,
            contenu=contenu,
            contexte=contexte,
            locuteurs=locuteurs,
            revision=source.revision + 1,
            revision_projet=(
                source.revision_projet + 1 if source.revision_projet else None
            ),
        )
        self.sources[self.sources.index(source)] = modifiee
        self.analyses = [
            analyse
            for analyse in self.analyses
            if analyse.transcript_id != transcript_id
        ]
        self.fonctionnalites = [
            feature
            for feature in self.fonctionnalites
            if feature["transcript_id"] != transcript_id
        ]
        self.jobs = [job for job in self.jobs if job.transcript_id != transcript_id]
        return modifiee

    def supprimer(self, transcript_id: int) -> bool:
        source = self.obtenir(transcript_id)
        if source is None:
            return False
        self.sources.remove(source)
        self.analyses = [
            analyse
            for analyse in self.analyses
            if analyse.transcript_id != transcript_id
        ]
        self.jobs = [job for job in self.jobs if job.transcript_id != transcript_id]
        return True

    def obtenir_analyse(self, transcript_id: int) -> AnalyseTranscriptPdf | None:
        return next(
            (
                analyse
                for analyse in self.analyses
                if analyse.transcript_id == transcript_id
            ),
            None,
        )

    def creer_job(
        self, transcript_id: int, relancer: bool = False
    ) -> JobAnalyseTranscript:
        source = self.obtenir(transcript_id)
        if source is None:
            raise ValueError("Transcript confirmé introuvable.")
        job = next(
            (
                item
                for item in self.jobs
                if item.transcript_id == transcript_id
                and item.revision == source.revision
            ),
            None,
        )
        if job is None:
            job = JobAnalyseTranscript(
                self._prochain_job,
                transcript_id,
                source.revision,
                source.revision_projet,
                "attente",
                None,
                None,
            )
            self._prochain_job += 1
            self.jobs.append(job)
        elif relancer and job.statut == "echec":
            job = job._replace(statut="attente", jeton=None, bail_jusqua=None)
            self.jobs[
                self.jobs.index(next(item for item in self.jobs if item.id == job.id))
            ] = job
        return job

    def obtenir_job(self, transcript_id: int) -> JobAnalyseTranscript | None:
        return next(
            (job for job in reversed(self.jobs) if job.transcript_id == transcript_id),
            None,
        )

    def reclamer_job(
        self, job_id: int, duree_bail_secondes: int = 360
    ) -> JobAnalyseTranscript | None:
        job = next((item for item in self.jobs if item.id == job_id), None)
        if (
            job is None
            or job.statut != "attente"
            and not (
                job.statut == "en_cours"
                and job.bail_jusqua
                and job.bail_jusqua < datetime.now()
            )
        ):
            return None
        job = job._replace(
            statut="en_cours",
            jeton=str(uuid4()),
            bail_jusqua=datetime.now() + timedelta(seconds=duree_bail_secondes),
        )
        self.jobs[
            self.jobs.index(next(item for item in self.jobs if item.id == job_id))
        ] = job
        return job

    def finaliser(
        self,
        job: JobAnalyseTranscript,
        analyse: dict[str, object],
        fonctionnalites: list[dict[str, object]],
        schema_version: str,
        prompt_version: str,
    ) -> bool:
        courant = self.obtenir_job(job.transcript_id)
        source = self.obtenir(job.transcript_id)
        if (
            courant is None
            or source is None
            or courant.jeton != job.jeton
            or source.revision != job.revision
            or source.revision_projet != job.revision_projet
        ):
            return False
        self.analyses.append(
            AnalyseTranscriptPdf(
                len(self.analyses) + 1,
                job.transcript_id,
                job.revision,
                source.type_source,
                analyse,
                schema_version,
                prompt_version,
                datetime.now(),
            )
        )
        self.fonctionnalites.extend(
            [{"transcript_id": job.transcript_id, **item} for item in fonctionnalites]
        )
        self.jobs[self.jobs.index(courant)] = courant._replace(
            statut="termine", jeton=None, bail_jusqua=None
        )
        return True

    def echouer(self, job_id: int, jeton: str, message: str) -> None:
        job = next((item for item in self.jobs if item.id == job_id), None)
        if job and job.jeton == jeton:
            self.jobs[self.jobs.index(job)] = job._replace(
                statut="echec", jeton=None, bail_jusqua=None
            )

    def lister_jobs_a_reprendre(self) -> list[int]:
        return [
            job.id
            for job in self.jobs
            if job.statut == "attente"
            or (
                job.statut == "en_cours"
                and job.bail_jusqua
                and job.bail_jusqua < datetime.now()
            )
        ]
