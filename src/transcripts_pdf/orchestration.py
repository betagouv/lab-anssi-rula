import re
import logging
import time
from datetime import date
from typing import NamedTuple

from transcripts_pdf.analyse import ErreurAnalysePdf, ServiceAnalysePdf
from transcripts_pdf.depot import (
    AnalyseTranscriptPdf,
    DepotTranscriptsPdf,
    JobAnalyseTranscript,
    SourceTranscriptPdf,
)
from transcripts_pdf.service import Locuteur

_JOURNAL = logging.getLogger("uvicorn.error")


class SourcePdfInvalide(ValueError):
    pass


class ResultatAnalyseSource(NamedTuple):
    job: JobAnalyseTranscript
    analyse: AnalyseTranscriptPdf | None


class ServiceTranscriptsPdf:
    def __init__(
        self,
        depot: DepotTranscriptsPdf,
        analyseur: ServiceAnalysePdf,
        delai_albert: int = 180,
    ) -> None:
        self._depot = depot
        self._analyseur = analyseur
        self._duree_bail_secondes = max(360, delai_albert + 60)

    def confirmer(
        self,
        type_source: str,
        nom_source: str,
        produit_id: int,
        projet_id: int | None,
        date_entretien: date | None,
        contenu: str,
        contexte: str,
        locuteurs: list[Locuteur],
    ) -> SourceTranscriptPdf:
        if type_source not in {"produit", "bizdev"}:
            raise SourcePdfInvalide("Le type de source est invalide.")
        correspondance = re.fullmatch(
            r"(?:reunion-_[a-z]{3}-[a-z]{4}-[a-z]{3}_-du-\d{4}-\d{2}-\d{2}-a-\d{2}_\d{2}\.pdf|"
            r"reunion--[a-z]{3}-[a-z]{4}-[a-z]{3}--du-\d{4}-\d{2}-\d{2}-a-\d{2}-\d{2}\.pdf|"
            r"transcript-(?P<type_source>produit|bizdev)-(?:sans-date|\d{4}-\d{2}-\d{2})-[0-9a-f]{8}\.pdf)",
            nom_source,
            re.IGNORECASE,
        )
        type_nom = correspondance.group("type_source") if correspondance else None
        if correspondance is None or (
            type_nom is not None and type_nom.casefold() != type_source
        ):
            raise SourcePdfInvalide("Le nom de source est invalide.")
        date_validee = self._verifier(
            type_source, produit_id, projet_id, date_entretien, contenu, locuteurs
        )
        return self._depot.ajouter(
            type_source,
            produit_id,
            projet_id,
            nom_source,
            date_validee,
            contenu,
            contexte,
            [locuteur._asdict() for locuteur in locuteurs],
        )

    def obtenir(self, transcript_id: int) -> SourceTranscriptPdf | None:
        return self._depot.obtenir(transcript_id)

    def lister(self, produit_id: int) -> list[SourceTranscriptPdf]:
        return self._depot.lister(produit_id)

    def modifier(
        self,
        transcript_id: int,
        date_entretien: date | None,
        contenu: str,
        contexte: str,
        locuteurs: list[Locuteur],
    ) -> SourceTranscriptPdf | None:
        source = self._depot.obtenir(transcript_id)
        if source is None:
            return None
        date_validee = self._verifier(
            source.type_source,
            source.produit_id,
            source.projet_id,
            date_entretien,
            contenu,
            locuteurs,
        )
        return self._depot.modifier(
            transcript_id,
            date_validee,
            contenu,
            contexte,
            [locuteur._asdict() for locuteur in locuteurs],
        )

    def supprimer(self, transcript_id: int) -> bool:
        return self._depot.supprimer(transcript_id)

    def obtenir_analyse(self, transcript_id: int):
        return self._depot.obtenir_analyse(transcript_id)

    def demarrer_analyse(
        self, transcript_id: int, relancer: bool = False
    ) -> ResultatAnalyseSource:
        source = self._depot.obtenir(transcript_id)
        if source is None:
            raise SourcePdfInvalide("Source introuvable.")
        analyse = self._depot.obtenir_analyse(transcript_id)
        if analyse is not None and analyse.revision == source.revision:
            return ResultatAnalyseSource(self._depot.creer_job(transcript_id), analyse)
        job = self._depot.creer_job(transcript_id, relancer)
        return ResultatAnalyseSource(job, None)

    def executer_job(self, job_id: int) -> None:
        job = self._depot.reclamer_job(job_id, self._duree_bail_secondes)
        if job is None or job.jeton is None:
            return
        source = self._depot.obtenir(job.transcript_id)
        if (
            source is None
            or source.revision != job.revision
            or source.revision_projet != job.revision_projet
        ):
            self._depot.echouer(job.id, job.jeton, "Le corpus a changé.")
            return
        debut_analyse = time.monotonic()
        try:
            analyse = self._analyseur.analyser(
                source.type_source,
                source.contenu,
                source.contexte,
                source.locuteurs,
                "pdf-v1",
            )
        except ErreurAnalysePdf as erreur:
            mesures = erreur.mesures
            _JOURNAL.error(
                "transcript_pdf_analysis_failed transcript_id=%s job_id=%s phase=%s code=%s exception_type=ErreurAnalysePdf duration_s=%s model=%s temperature=%s top_p=%s reasoning=%s budget=%s http_status=%s finish_reason=%s content_type=%s content_chars=%s reasoning_type=%s reasoning_chars=%s refus_present=%s choices=%s message_keys=%s reference_index=%s tour_id=%s speaker_id=%s tokens_tour=%s token_debut=%s token_fin=%s",
                source.id,
                job.id,
                erreur.phase,
                erreur.code,
                erreur.duree_secondes,
                mesures.get("modele"),
                mesures.get("temperature"),
                mesures.get("top_p"),
                mesures.get("raisonnement"),
                mesures.get("budget_completion"),
                mesures.get("statut_http"),
                mesures.get("finish_reason"),
                mesures.get("contenu_type"),
                mesures.get("contenu_caracteres"),
                mesures.get("raisonnement_type"),
                mesures.get("raisonnement_caracteres"),
                mesures.get("refus_present"),
                mesures.get("choix_nombre"),
                mesures.get("message_champs_nombre"),
                mesures.get("reference_index"),
                mesures.get("tour_id"),
                mesures.get("speaker_id"),
                mesures.get("tokens_tour"),
                mesures.get("token_debut"),
                mesures.get("token_fin"),
            )
            self._depot.echouer(job.id, job.jeton, "Analyse impossible.")
            return
        except Exception as erreur:
            _JOURNAL.error(
                "transcript_pdf_analysis_failed transcript_id=%s job_id=%s phase=analyse code=exception_inattendue exception_type=%s duration_s=%s",
                source.id,
                job.id,
                type(erreur).__name__,
                round(time.monotonic() - debut_analyse, 3),
            )
            self._depot.echouer(job.id, job.jeton, "Analyse impossible.")
            return
        debut_finalisation = time.monotonic()
        try:
            finalise = self._depot.finaliser(
                job,
                analyse.contenu,
                analyse.fonctionnalites,
                analyse.schema_version,
                f"{source.type_source}-v6",
            )
            if not finalise:
                _JOURNAL.error(
                    "transcript_pdf_analysis_failed transcript_id=%s job_id=%s phase=finalisation code=claim_ou_revision_invalide exception_type=none duration_s=%s",
                    source.id,
                    job.id,
                    round(time.monotonic() - debut_finalisation, 3),
                )
                self._depot.echouer(job.id, job.jeton, "Analyse impossible.")
        except Exception as erreur:
            _JOURNAL.error(
                "transcript_pdf_analysis_failed transcript_id=%s job_id=%s phase=finalisation code=exception_persistance exception_type=%s duration_s=%s",
                source.id,
                job.id,
                type(erreur).__name__,
                round(time.monotonic() - debut_finalisation, 3),
            )
            self._depot.echouer(job.id, job.jeton, "Analyse impossible.")

    def lister_jobs_a_reprendre(self) -> list[int]:
        return self._depot.lister_jobs_a_reprendre()

    @staticmethod
    def _verifier(
        type_source: str,
        produit_id: int,
        projet_id: int | None,
        date_entretien: date | None,
        contenu: str,
        locuteurs: list[Locuteur],
    ) -> date:
        if type_source not in {"produit", "bizdev"}:
            raise SourcePdfInvalide("Type de source invalide.")
        if produit_id < 1:
            raise SourcePdfInvalide("Le produit est obligatoire.")
        if (type_source == "produit") != (projet_id is not None):
            raise SourcePdfInvalide("Le rattachement produit/projet est invalide.")
        if date_entretien is None:
            raise SourcePdfInvalide("La date de l’entretien est obligatoire.")
        if not contenu.strip():
            raise SourcePdfInvalide("Le transcript est vide.")
        ids = re.findall(r"(?m)^(SPEAKER_\d{2}):", contenu)
        connus = {locuteur.identifiant for locuteur in locuteurs}
        if set(ids) != connus:
            raise SourcePdfInvalide("Les identifiants de locuteur sont invalides.")
        if any(
            locuteur.role not in {"interne", "externe", "indetermine"}
            for locuteur in locuteurs
        ):
            raise SourcePdfInvalide("Le rôle de locuteur est invalide.")
        return date_entretien
