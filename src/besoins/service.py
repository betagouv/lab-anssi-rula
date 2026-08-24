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

    def lister(self, source: str | None = None) -> list[BesoinDetecte]:
        return self._depot.lister(source)

    def analyser(self, source: str) -> list[BesoinDetecte]:
        if source == "transcript":
            return self._analyser_transcripts()
        if source == "idee":
            return self._analyser_idees()
        if source == "retour_bizdev":
            return self._analyser_retours()
        raise SourceBesoinInconnue(source)

    def _analyser_transcripts(self) -> list[BesoinDetecte]:
        for transcript in self._depot_transcripts.lister():
            try:
                self._service_fonctionnalites.calculer(transcript.id)
            except FonctionnalitesDejaExistantes:
                pass
        besoins: list[tuple[int, str, str, str | None, int | None]] = [
            (f.id, f.contenu, f.contenu, f.verbatim, f.transcript_id)
            for f in self._depot_fonctionnalites.lister()
        ]
        return self._depot.remplacer_source("transcript", besoins)

    def _analyser_idees(self) -> list[BesoinDetecte]:
        besoins: list[tuple[int, str, str, str | None, int | None]] = []
        for idee in self._depot_idees.lister():
            nom = self._nom_generique(self._prompt_featurebase, idee.titre)
            besoins.append((idee.id, idee.titre, nom, None, None))
        return self._depot.remplacer_source("idee", besoins)

    def _analyser_retours(self) -> list[BesoinDetecte]:
        besoins: list[tuple[int, str, str, str | None, int | None]] = []
        for retour in self._depot_retours.lister():
            contexte = "\n".join(
                value for value in [retour.verbatim, retour.categorie, retour.item, retour.role] if value
            )
            nom = self._nom_generique(self._prompt_bizdev, contexte)
            besoins.append((retour.id, retour.verbatim, nom, retour.verbatim, None))
        return self._depot.remplacer_source("retour_bizdev", besoins)

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
