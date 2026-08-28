import json

from adaptateurs.albert import AdaptateurAlbert
from besoins.dependances import DependancesBesoins
from besoins.depot import BesoinDetecte
from fonctionnalites.service import FonctionnalitesDejaExistantes


class SourceBesoinInconnue(ValueError):
    pass


class ServiceBesoinsDetectes:
    def __init__(
        self,
        dependances: DependancesBesoins,
        albert: AdaptateurAlbert,
        prompts: tuple[str, str],
    ) -> None:
        self._depot = dependances.depot
        self._depot_transcripts = dependances.depot_transcripts
        self._depot_fonctionnalites = dependances.depot_fonctionnalites
        self._service_fonctionnalites = dependances.service_fonctionnalites
        self._depot_idees = dependances.depot_idees
        self._depot_retours = dependances.depot_retours
        self._albert = albert
        self._prompt_featurebase, self._prompt_bizdev = prompts

    def lister(self, source: str | None = None, produit_id: int | None = None) -> list[BesoinDetecte]:
        return self._depot.lister(source, produit_id)

    def analyser(self, source: str, produit_id: int | None = None) -> list[BesoinDetecte]:
        if produit_id is None:
            produits = sorted(self._produits_de_source(source))
            if produits:
                return [besoin for produit in produits for besoin in self.analyser(source, produit)]
        return self._depot.remplacer_source(source, self.preparer(source, produit_id), produit_id)

    def remplacer(self, source: str, besoins: list[tuple[int, str, str, str | None, int | None]], produit_id: int | None = None) -> list[BesoinDetecte]:
        return self._depot.remplacer_source(source, besoins, produit_id)

    def restaurer(self, besoins: list[BesoinDetecte], produit_id: int) -> None:
        self._depot.restaurer(besoins, produit_id)

    def preparer(self, source: str, produit_id: int | None = None) -> list[tuple[int, str, str, str | None, int | None]]:
        if source == "transcript":
            return self._preparer_transcripts(produit_id)
        if source == "idee":
            return self._preparer_idees(produit_id)
        if source == "retour_bizdev":
            return self._preparer_retours(produit_id)
        raise SourceBesoinInconnue(source)

    def _produits_de_source(self, source: str) -> set[int]:
        if source == "transcript":
            return {transcript.produit_id for transcript in self._depot_transcripts.lister()}
        if source == "idee":
            return {idee.produit_id for idee in self._depot_idees.lister()}
        if source == "retour_bizdev":
            return {retour.produit_id for retour in self._depot_retours.lister()}
        raise SourceBesoinInconnue(source)

    def _preparer_transcripts(self, produit_id: int | None = None) -> list[tuple[int, str, str, str | None, int | None]]:
        transcripts = [t for t in self._depot_transcripts.lister() if produit_id is None or t.produit_id == produit_id]
        transcript_ids = {t.id for t in transcripts}
        for transcript in transcripts:
            try:
                self._service_fonctionnalites.calculer(transcript.id)
            except FonctionnalitesDejaExistantes:
                pass
        besoins: list[tuple[int, str, str, str | None, int | None]] = [
            (f.id, f.contenu, f.contenu, f.verbatim, f.transcript_id)
            for f in self._depot_fonctionnalites.lister()
            if f.transcript_id in transcript_ids
        ]
        return besoins

    def _preparer_idees(self, produit_id: int | None = None) -> list[tuple[int, str, str, str | None, int | None]]:
        besoins: list[tuple[int, str, str, str | None, int | None]] = []
        for idee in self._depot_idees.lister(produit_id, None):
            nom = self._nom_generique(self._prompt_featurebase, idee.titre)
            besoins.append((idee.id, idee.titre, nom, None, None))
        return besoins

    def _preparer_retours(self, produit_id: int | None = None) -> list[tuple[int, str, str, str | None, int | None]]:
        besoins: list[tuple[int, str, str, str | None, int | None]] = []
        for retour in self._depot_retours.lister(produit_id, None):
            contexte = "\n".join(
                value for value in [retour.verbatim, retour.categorie, retour.item, retour.role] if value
            )
            nom = self._nom_generique(self._prompt_bizdev, contexte)
            besoins.append((retour.id, retour.verbatim, nom, retour.verbatim, None))
        return besoins

    def _nom_generique(self, prompt: str, texte: str) -> str:
        reponse = self._albert.completer(
            [{"role": "system", "content": prompt}, {"role": "user", "content": texte}],
            temperature=0.1,
        ).strip()
        try:
            valeur = json.loads(reponse)
            if isinstance(valeur, dict) and isinstance(valeur.get("fonctionnalite"), str):
                return valeur["fonctionnalite"].strip()
            if isinstance(valeur, list) and valeur and isinstance(valeur[0], dict) and isinstance(valeur[0].get("fonctionnalite"), str):
                return valeur[0]["fonctionnalite"].strip()
            if isinstance(valeur, str):
                return valeur.strip()
        except json.JSONDecodeError:
            pass
        return reponse.strip('"')
