import re
from datetime import date

from transcripts_pdf.depot import DepotTranscriptsPdf, SourceTranscriptPdf
from transcripts_pdf.service import Locuteur


class SourcePdfInvalide(ValueError):
    pass


class ServiceTranscriptsPdf:
    def __init__(self, depot: DepotTranscriptsPdf) -> None:
        self._depot = depot

    def confirmer(
        self,
        type_source: str,
        nom_source: str,
        produit_id: int,
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
            type_source, produit_id, date_entretien, contenu, locuteurs
        )
        return self._depot.ajouter(
            type_source,
            produit_id,
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

    @staticmethod
    def _verifier(
        type_source: str,
        produit_id: int,
        date_entretien: date | None,
        contenu: str,
        locuteurs: list[Locuteur],
    ) -> date:
        if type_source not in {"produit", "bizdev"}:
            raise SourcePdfInvalide("Type de source invalide.")
        if produit_id < 1:
            raise SourcePdfInvalide("Le produit est obligatoire.")
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
