import csv
import io

from retours_bizdev.depot import DepotRetoursBizDev, Retour, RetourBrut


class ServiceRetoursBizDev:
    def __init__(self, depot: DepotRetoursBizDev) -> None:
        self._depot = depot

    def importer(self, contenu_csv: str) -> list[Retour]:
        reader = csv.DictReader(io.StringIO(contenu_csv.lstrip("﻿")))
        retours = [
            RetourBrut(
                verbatim=r["Verbatim"],
                categorie=r.get("Catégorie") or None,
                item=r.get("Item") or None,
                role=r.get("Rôle du user") or None,
                qui=r.get("Qui ?") or None,
                date_retour=r.get("Date") or None,
            )
            for r in reader
            if r["Verbatim"].strip()
        ]
        return self._depot.remplacer_tous(retours)

    def lister(self) -> list[Retour]:
        return self._depot.lister()
