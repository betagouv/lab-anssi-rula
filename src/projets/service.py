from adaptateurs.albert import AdaptateurAlbert
from projets.depot import DepotProjets, ScanProjet, SourceAnalyseProjet


class ProjetIntrouvable(ValueError):
    pass


class ProjetDejaExistant(ValueError):
    pass


class CorpusProjetModifie(ValueError):
    pass


class ServiceScansProjets:
    def __init__(
        self, depot: DepotProjets, albert: AdaptateurAlbert, prompt: str
    ) -> None:
        self._depot = depot
        self._albert = albert
        self._prompt = prompt

    def generer(self, projet_id: int) -> ScanProjet:
        projet = self._depot.obtenir(projet_id)
        if not projet:
            raise ProjetIntrouvable
        sources = self._depot.lister_sources_analyse(projet_id)
        contenu = "\n\n".join(self._formater_source(source) for source in sources)
        scan = self._depot.enregistrer_scan_si_revision(
            projet_id,
            projet.revision_corpus,
            self._albert.completer(
                [
                    {"role": "system", "content": self._prompt},
                    {"role": "user", "content": contenu},
                ],
                temperature=0.3,
            ),
        )
        if scan is None:
            raise CorpusProjetModifie
        return scan

    @staticmethod
    def _formater_source(source: SourceAnalyseProjet) -> str:
        if source.type_source == "ux":
            return (
                f"## {source.participant}\n{source.contenu}\n{source.note_moderateur}"
            )
        locuteurs = ", ".join(
            f"{locuteur['identifiant']}: {locuteur['role']}"
            for locuteur in source.locuteurs
        )
        return (
            f"## Transcript {source.type_source} — {source.date_entretien}\n"
            f"{locuteurs}\n{source.contexte}\n{source.contenu}"
        )
