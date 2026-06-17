import csv
import io

from idees.depot import DepotIdees, Idee, IdeeBrute


class ServiceIdees:
    def __init__(self, depot: DepotIdees) -> None:
        self._depot = depot

    def importer(self, contenu_csv: str) -> list[Idee]:
        reader = csv.DictReader(io.StringIO(contenu_csv.lstrip("﻿")))
        idees = [
            IdeeBrute(
                titre=f"{r['Title']}: {r['Content']}" if r["Content"].strip() else r["Title"],
                nb_votes=int(r["Upvote Count"] or 0),
            )
            for r in reader
        ]
        return self._depot.remplacer_toutes(idees)

    def lister(self) -> list[Idee]:
        return self._depot.lister()
