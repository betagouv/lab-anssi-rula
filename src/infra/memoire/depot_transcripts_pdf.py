from datetime import date, datetime

from transcripts_pdf.depot import DepotTranscriptsPdf, SourceTranscriptPdf


class DepotTranscriptsPdfMemoire(DepotTranscriptsPdf):
    def __init__(self) -> None:
        self.sources: list[SourceTranscriptPdf] = []
        self._prochain_id = 1

    def ajouter(
        self,
        type_source: str,
        produit_id: int,
        nom_source: str,
        date_entretien: date,
        contenu: str,
        contexte: str,
        locuteurs: list[dict[str, str]],
    ) -> SourceTranscriptPdf:
        source = SourceTranscriptPdf(
            self._prochain_id,
            type_source,
            produit_id,
            nom_source,
            date_entretien,
            contenu,
            contexte,
            locuteurs,
            datetime.now(),
        )
        self.sources.append(source)
        self._prochain_id += 1
        return source

    def obtenir(self, transcript_id: int) -> SourceTranscriptPdf | None:
        return next(
            (source for source in self.sources if source.id == transcript_id), None
        )

    def lister(self, produit_id: int) -> list[SourceTranscriptPdf]:
        return sorted(
            (source for source in self.sources if source.produit_id == produit_id),
            key=lambda source: (source.cree_le, source.id),
            reverse=True,
        )

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
        )
        self.sources[self.sources.index(source)] = modifiee
        return modifiee

    def supprimer(self, transcript_id: int) -> bool:
        source = self.obtenir(transcript_id)
        if source is None:
            return False
        self.sources.remove(source)
        return True
