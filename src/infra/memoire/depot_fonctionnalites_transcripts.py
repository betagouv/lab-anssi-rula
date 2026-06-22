from datetime import datetime

from fonctionnalites.depot import DepotFonctionnalitesTranscripts, Fonctionnalite


class DepotFonctionnalitesTranscriptsMemoire(DepotFonctionnalitesTranscripts):
    def __init__(self) -> None:
        self._fonctionnalites: list[Fonctionnalite] = []
        self._prochain_id = 1

    def ajouter_toutes(self, transcript_id: int, items: list[tuple[str, str | None]]) -> list[Fonctionnalite]:
        ajoutees = [
            Fonctionnalite(id=self._prochain_id + i, transcript_id=transcript_id, contenu=c, verbatim=v, cree_le=datetime.now())
            for i, (c, v) in enumerate(items)
        ]
        self._fonctionnalites.extend(ajoutees)
        self._prochain_id += len(items)
        return ajoutees

    def obtenir_par_transcript(self, transcript_id: int) -> list[Fonctionnalite]:
        return [f for f in self._fonctionnalites if f.transcript_id == transcript_id]

    def lister(self) -> list[Fonctionnalite]:
        return list(self._fonctionnalites)
