from datetime import date, datetime

from projets.depot import DepotProjets, Entretien, Projet, ScanProjet, SourceProjet
from projets.service import ProjetDejaExistant


class DepotProjetsDeTest(DepotProjets):
    def __init__(self) -> None:
        self.projets: list[Projet] = []
        self.entretiens: list[Entretien] = []
        self.scans: dict[int, ScanProjet] = {}

    def ajouter(self, produit_id: int, nom: str, brief: str) -> Projet:
        if any(
            projet.produit_id == produit_id
            and projet.nom.strip().lower() == nom.strip().lower()
            for projet in self.projets
        ):
            raise ProjetDejaExistant
        projet = Projet(len(self.projets) + 1, produit_id, nom, brief, datetime.now())
        self.projets.append(projet)
        return projet

    def lister(self, produit_id: int) -> list[Projet]:
        return [projet for projet in self.projets if projet.produit_id == produit_id]

    def obtenir(self, id: int) -> Projet | None:
        return next((projet for projet in self.projets if projet.id == id), None)

    def supprimer(self, id: int) -> bool:
        projet = self.obtenir(id)
        if not projet:
            return False
        self.projets.remove(projet)
        self.entretiens = [
            entretien for entretien in self.entretiens if entretien.projet_id != id
        ]
        self.scans.pop(id, None)
        return True

    def ajouter_entretien(
        self,
        projet_id: int,
        participant: str,
        date_entretien: date,
        moderateur: str,
        contenu: str,
        note_moderateur: str,
    ) -> Entretien:
        entretien = Entretien(
            len(self.entretiens) + 1,
            projet_id,
            participant,
            date_entretien,
            moderateur,
            contenu,
            note_moderateur,
            datetime.now(),
        )
        self.entretiens.append(entretien)
        return entretien

    def ajouter_source(
        self,
        produit_id: int,
        projet_id: int | None,
        nom: str | None,
        brief: str,
        participant: str,
        date_entretien: date,
        moderateur: str,
        contenu: str,
        note_moderateur: str,
    ) -> SourceProjet:
        projet = self.obtenir(projet_id) if projet_id is not None else None
        if projet is None:
            projet = self.ajouter(produit_id, nom or "", brief)
        return SourceProjet(
            projet,
            self.ajouter_entretien(
                projet.id,
                participant,
                date_entretien,
                moderateur,
                contenu,
                note_moderateur,
            ),
        )

    def lister_entretiens(self, projet_id: int) -> list[Entretien]:
        return [
            entretien
            for entretien in self.entretiens
            if entretien.projet_id == projet_id
        ]

    def enregistrer_scan(self, projet_id: int, brouillon: str) -> ScanProjet:
        scan = ScanProjet(projet_id, brouillon, None, datetime.now(), datetime.now())
        self.scans[projet_id] = scan
        return scan

    def obtenir_scan(self, projet_id: int) -> ScanProjet | None:
        return self.scans.get(projet_id)

    def modifier_scan(self, projet_id: int, brouillon: str) -> ScanProjet | None:
        scan = self.scans.get(projet_id)
        if not scan:
            return None
        return self.enregistrer_scan(projet_id, brouillon)

    def valider_scan(self, projet_id: int) -> ScanProjet | None:
        scan = self.scans.get(projet_id)
        if not scan:
            return None
        valide = ScanProjet(
            projet_id, scan.brouillon, scan.brouillon, scan.cree_le, datetime.now()
        )
        self.scans[projet_id] = valide
        return valide
