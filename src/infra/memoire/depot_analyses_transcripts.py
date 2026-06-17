from datetime import datetime

from analyses.depot import AnalyseTranscript, DepotAnalysesTranscripts


class DepotAnalysesTranscriptsMemoire(DepotAnalysesTranscripts):
    def __init__(self) -> None:
        self._analyses: list[AnalyseTranscript] = []
        self._prochain_id = 1

    def ajouter(self, transcript_id: int, contenu: str) -> AnalyseTranscript:
        analyse = AnalyseTranscript(
            id=self._prochain_id,
            transcript_id=transcript_id,
            contenu=contenu,
            cree_le=datetime.now(),
        )
        self._analyses.append(analyse)
        self._prochain_id += 1
        return analyse

    def obtenir_par_transcript(self, transcript_id: int) -> AnalyseTranscript | None:
        return next((a for a in self._analyses if a.transcript_id == transcript_id), None)

    def lister(self) -> list[AnalyseTranscript]:
        return list(self._analyses)
