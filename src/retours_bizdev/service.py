import csv
import io

from retours_bizdev.depot import DepotRetoursBizDev, Retour, RetourBrut
from nettoyage_texte import nettoie_texte


class ServiceRetoursBizDev:
    def __init__(self, depot: DepotRetoursBizDev) -> None:
        self._depot = depot

    def importer(
        self, produit_id: int, contenu_csv: str, projet_id: int | None = None
    ) -> list[Retour]:
        reader = csv.DictReader(io.StringIO(contenu_csv.lstrip("﻿")))
        retours = [
            RetourBrut(
                verbatim=nettoie_texte(r["Verbatim"]),
                categorie=nettoie_texte(r["Catégorie"]) if r.get("Catégorie") else None,
                item=nettoie_texte(r["Item"]) if r.get("Item") else None,
                role=nettoie_texte(r["Rôle du user"])
                if r.get("Rôle du user")
                else None,
                qui=nettoie_texte(r["Qui ?"]) if r.get("Qui ?") else None,
                date_retour=nettoie_texte(r["Date"]) if r.get("Date") else None,
            )
            for r in reader
            if r["Verbatim"].strip()
        ]
        return self._depot.remplacer_tous(produit_id, retours, projet_id)

    def lister(
        self, produit_id: int | None = None, projet_id: int | None = None
    ) -> list[Retour]:
        return self._depot.lister(produit_id, projet_id)
