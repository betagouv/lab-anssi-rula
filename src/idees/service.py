import csv
import io

from idees.depot import DepotIdees, Idee, IdeeBrute
from nettoyage_texte import nettoie_texte


class ServiceIdees:
    def __init__(self, depot: DepotIdees) -> None:
        self._depot = depot

    def importer(
        self, produit_id: int, contenu_csv: str, projet_id: int | None = None
    ) -> list[Idee]:
        reader = csv.DictReader(io.StringIO(contenu_csv.lstrip("﻿")))
        idees = [
            IdeeBrute(
                titre=(
                    f"{nettoie_texte(r['Title'])}: {nettoie_texte(r['Content'])}"
                    if r["Content"].strip()
                    else nettoie_texte(r["Title"])
                ),
                nb_votes=int(r["Upvote Count"] or 0),
            )
            for r in reader
        ]
        return self._depot.remplacer_toutes(produit_id, idees, projet_id)

    def lister(
        self, produit_id: int | None = None, projet_id: int | None = None
    ) -> list[Idee]:
        return self._depot.lister(produit_id, projet_id)
