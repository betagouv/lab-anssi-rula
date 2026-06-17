import json

from adaptateurs.albert import AdaptateurAlbert
from fonctionnalites.depot import DepotFonctionnalitesTranscripts, Fonctionnalite
from transcripts.depot import DepotTranscripts


class FonctionnalitesDejaExistantes(Exception):
    pass


class ServiceFonctionnalites:
    def __init__(
        self,
        depot_transcripts: DepotTranscripts,
        depot_fonctionnalites: DepotFonctionnalitesTranscripts,
        albert: AdaptateurAlbert,
        systeme_prompt: str,
    ) -> None:
        self._depot_transcripts = depot_transcripts
        self._depot_fonctionnalites = depot_fonctionnalites
        self._albert = albert
        self._systeme_prompt = systeme_prompt

    def calculer(self, transcript_id: int) -> list[Fonctionnalite]:
        t = self._depot_transcripts.obtenir(transcript_id)
        if t is None:
            raise ValueError(f"transcript {transcript_id} introuvable")
        if self._depot_fonctionnalites.obtenir_par_transcript(transcript_id):
            raise FonctionnalitesDejaExistantes
        reponse = self._albert.completer(
            [{"role": "system", "content": self._systeme_prompt}, {"role": "user", "content": t.contenu}],
            temperature=0.1,
        )
        return self._depot_fonctionnalites.ajouter_toutes(transcript_id, json.loads(reponse))

    def obtenir(self, transcript_id: int) -> list[Fonctionnalite]:
        return self._depot_fonctionnalites.obtenir_par_transcript(transcript_id)

    def lister(self) -> list[Fonctionnalite]:
        return self._depot_fonctionnalites.lister()
