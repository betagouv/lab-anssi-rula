from adaptateurs.albert import AdaptateurAlbert
from projets.depot import DepotProjets, ScanProjet


class ProjetIntrouvable(ValueError):
    pass


class ProjetDejaExistant(ValueError):
    pass


class ServiceScansProjets:
    def __init__(
        self, depot: DepotProjets, albert: AdaptateurAlbert, prompt: str
    ) -> None:
        self._depot = depot
        self._albert = albert
        self._prompt = prompt

    def generer(self, projet_id: int) -> ScanProjet:
        entretiens = self._depot.lister_entretiens(projet_id)
        if not self._depot.obtenir(projet_id):
            raise ProjetIntrouvable
        contenu = "\n\n".join(
            f"## {e.participant}\n{e.contenu}\n{e.note_moderateur}" for e in entretiens
        )
        return self._depot.enregistrer_scan(
            projet_id,
            self._albert.completer(
                [
                    {"role": "system", "content": self._prompt},
                    {"role": "user", "content": contenu},
                ],
                temperature=0.3,
            ),
        )
