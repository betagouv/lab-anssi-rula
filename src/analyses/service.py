from adaptateurs.albert import AdaptateurAlbert
from analyses.depot import AnalyseTranscript, DepotAnalysesTranscripts
from transcripts.depot import DepotTranscripts


class AnalyseDejaExistante(Exception):
    pass


class ServiceAnalyse:
    def __init__(
        self,
        depot_transcripts: DepotTranscripts,
        depot_analyses: DepotAnalysesTranscripts,
        albert: AdaptateurAlbert,
        systeme_prompt: str,
    ) -> None:
        self._depot_transcripts = depot_transcripts
        self._depot_analyses = depot_analyses
        self._albert = albert
        self._systeme_prompt = systeme_prompt

    def analyser(self, transcript_id: int) -> AnalyseTranscript:
        t = self._depot_transcripts.obtenir(transcript_id)
        if t is None:
            raise ValueError(f"transcript {transcript_id} introuvable")
        if self._depot_analyses.obtenir_par_transcript(transcript_id) is not None:
            raise AnalyseDejaExistante
        contenu = self._albert.completer(
            [
                {"role": "system", "content": self._systeme_prompt},
                {"role": "user", "content": t.contenu},
            ],
            temperature=0.3,
        )
        return self._depot_analyses.ajouter(transcript_id, contenu)

    def obtenir(self, transcript_id: int) -> AnalyseTranscript | None:
        return self._depot_analyses.obtenir_par_transcript(transcript_id)

    def lister(self) -> list[AnalyseTranscript]:
        return self._depot_analyses.lister()
