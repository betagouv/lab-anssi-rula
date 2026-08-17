from datetime import datetime

from besoins.depot import BesoinDetecte, DepotBesoinsDetectes


class DepotBesoinsDetectesMemoire(DepotBesoinsDetectes):
    def __init__(self) -> None:
        self._besoins: list[BesoinDetecte] = []
        self._prochain_id = 1

    def remplacer_source(self, source: str, besoins: list[tuple[int, str, str, str | None, int | None]]) -> list[BesoinDetecte]:
        self._besoins = [b for b in self._besoins if b.source != source]
        maintenant = datetime.now()
        for source_id, texte_original, nom_generique, verbatim, transcript_id in besoins:
            self._besoins.append(
                BesoinDetecte(
                    id=self._prochain_id,
                    source=source,
                    source_id=source_id,
                    texte_original=texte_original,
                    nom_generique=nom_generique,
                    verbatim=verbatim,
                    transcript_id=transcript_id,
                    statut="extrait",
                    cree_le=maintenant,
                )
            )
            self._prochain_id += 1
        return self.lister(source)

    def lister(self, source: str | None = None) -> list[BesoinDetecte]:
        besoins = self._besoins if source is None else [b for b in self._besoins if b.source == source]
        return sorted(besoins, key=lambda b: (b.source, b.id))
