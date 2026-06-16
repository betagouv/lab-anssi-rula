from datetime import date, datetime

from transcripts.depot import DepotTranscripts, Transcript


class DepotTranscriptsMemoire(DepotTranscripts):
    def __init__(self) -> None:
        self._transcripts: list[Transcript] = []
        self._prochain_id = 1

    def ajouter(self, identite_id: int, produit_id: int, date_entretien: date, contenu: str) -> Transcript:
        now = datetime.now()
        transcript = Transcript(
            id=self._prochain_id,
            identite_id=identite_id,
            produit_id=produit_id,
            date_entretien=date_entretien,
            contenu=contenu,
            cree_le=now,
            modifie_le=now,
        )
        self._transcripts.append(transcript)
        self._prochain_id += 1
        return transcript

    def lister(self) -> list[Transcript]:
        return list(self._transcripts)

    def obtenir(self, id: int) -> Transcript | None:
        return next((t for t in self._transcripts if t.id == id), None)

    def modifier(self, id: int, identite_id: int, produit_id: int, date_entretien: date, contenu: str) -> Transcript | None:
        for i, t in enumerate(self._transcripts):
            if t.id == id:
                updated = Transcript(
                    id=id,
                    identite_id=identite_id,
                    produit_id=produit_id,
                    date_entretien=date_entretien,
                    contenu=contenu,
                    cree_le=t.cree_le,
                    modifie_le=datetime.now(),
                )
                self._transcripts[i] = updated
                return updated
        return None

    def supprimer(self, id: int) -> bool:
        avant = len(self._transcripts)
        self._transcripts = [t for t in self._transcripts if t.id != id]
        return len(self._transcripts) < avant
