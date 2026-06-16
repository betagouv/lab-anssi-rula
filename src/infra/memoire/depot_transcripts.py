from datetime import date

from transcripts.depot import DepotTranscripts, Transcript


class DepotTranscriptsMemoire(DepotTranscripts):
    def __init__(self) -> None:
        self._transcripts: list[Transcript] = []
        self._prochain_id = 1

    def ajouter(self, identite_id: int, produit_id: int, date_entretien: date, contenu: str) -> Transcript:
        transcript = Transcript(
            id=self._prochain_id,
            identite_id=identite_id,
            produit_id=produit_id,
            date_entretien=date_entretien,
            contenu=contenu,
        )
        self._transcripts.append(transcript)
        self._prochain_id += 1
        return transcript

    def lister(self) -> list[Transcript]:
        return list(self._transcripts)
