from datetime import datetime

from besoins.depot import BesoinDetecte, DepotBesoinsDetectes


class DepotBesoinsDetectesMemoire(DepotBesoinsDetectes):
    def __init__(self) -> None:
        self._besoins: list[BesoinDetecte] = []
        self._prochain_id = 1

    def remplacer_source(self, source: str, besoins: list[tuple[int, str, str, str | None, int | None]], produit_id: int | None = None) -> list[BesoinDetecte]:
        self._besoins = [
            b for b in self._besoins
            if b.source != source or produit_id is not None and b.produit_id != produit_id
        ]
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
                    produit_id=produit_id,
                )
            )
            self._prochain_id += 1
        return self.lister(source, produit_id)

    def lister(self, source: str | None = None, produit_id: int | None = None) -> list[BesoinDetecte]:
        besoins = [
            b for b in self._besoins
            if (source is None or b.source == source)
            and (produit_id is None or b.produit_id == produit_id)
        ]
        return sorted(besoins, key=lambda b: (b.source, b.id))

    def restaurer(self, besoins: list[BesoinDetecte], produit_id: int) -> None:
        self._besoins = [b for b in self._besoins if b.produit_id != produit_id]
        self._besoins.extend(besoins)
        self._prochain_id = max((b.id for b in self._besoins), default=0) + 1
