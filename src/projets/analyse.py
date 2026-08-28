from abc import ABC, abstractmethod
from datetime import datetime
from typing import NamedTuple

from adaptateurs.albert import AdaptateurAlbert
from projets.depot import DepotProjets


ETAPES = (
    ("scan-neutre", "Scan neutre des données", 3),
    ("points-a-retenir", "Points à retenir", 4),
    ("thematisation", "Thématisation", 5),
)

BLOCS = (
    ("role", "Le rôle"),
    ("contexte_produit", "Contexte produit"),
    ("contexte_brief", "Contexte du brief"),
    ("contexte_projet", "Contexte du projet"),
    ("regles", "Les règles"),
    ("instructions_sortie", "Instructions de sortie"),
    ("consigne_scan-neutre", "Consigne — Scan neutre"),
    ("consigne_points-a-retenir", "Consigne — Points à retenir"),
    ("consigne_thematisation", "Consigne — Thématisation"),
)


class BlocPrompt(NamedTuple):
    cle: str
    libelle: str
    contenu: str
    ordre: int


class EtapeAnalyse(NamedTuple):
    projet_id: int
    cle: str
    libelle: str
    ordre: int
    prompt: str
    brouillon: str | None
    valide: str | None
    statut: str
    cree_le: datetime
    modifie_le: datetime


class ConfigurationAnalyse(NamedTuple):
    blocs: list[BlocPrompt]
    etapes: list[EtapeAnalyse]


class AnalyseProjetErreur(ValueError):
    pass


class EtapeInaccessible(AnalyseProjetErreur):
    pass


class EtapeAbsente(AnalyseProjetErreur):
    pass


class ProjetSansEntretien(AnalyseProjetErreur):
    pass


def assemble_prompt(blocs: list[BlocPrompt], etape: str) -> str:
    valeurs = {bloc.cle: bloc.contenu.strip() for bloc in blocs}
    cle_consigne = f"consigne_{etape}"
    ordre = (
        "role",
        "contexte_produit",
        "contexte_brief",
        "contexte_projet",
        "regles",
        cle_consigne,
        "consigne_etape",
        "instructions_sortie",
    )
    resultat: list[str] = []
    for cle in ordre:
        contenu = valeurs.get(cle, "")
        if contenu and (cle != "consigne_etape" or not valeurs.get(cle_consigne)):
            resultat.append(contenu)
    return "\n\n".join(resultat)


class DepotAnalyse(ABC):
    @abstractmethod
    def lister_blocs_produit(self, produit_id: int) -> list[BlocPrompt]:  # pragma: no cover
        ...

    @abstractmethod
    def lister_blocs_projet(self, projet_id: int) -> list[BlocPrompt]:  # pragma: no cover
        ...

    @abstractmethod
    def configuration_existe(self, projet_id: int) -> bool: ...

    @abstractmethod
    def enregistrer_configuration(
        self, projet_id: int, blocs: list[BlocPrompt]
    ) -> list[BlocPrompt]:  # pragma: no cover
        ...

    @abstractmethod
    def initialiser_etapes(self, projet_id: int) -> list[EtapeAnalyse]:  # pragma: no cover
        ...

    @abstractmethod
    def lister_etapes(self, projet_id: int) -> list[EtapeAnalyse]:  # pragma: no cover
        ...

    @abstractmethod
    def obtenir_etape(self, projet_id: int, cle: str) -> EtapeAnalyse | None:  # pragma: no cover
        ...

    @abstractmethod
    def enregistrer_etape(
        self, projet_id: int, cle: str, prompt: str, brouillon: str
    ) -> EtapeAnalyse:  # pragma: no cover
        ...

    @abstractmethod
    def modifier_etape(self, projet_id: int, cle: str, brouillon: str) -> EtapeAnalyse | None:  # pragma: no cover
        ...

    @abstractmethod
    def valider_etape(self, projet_id: int, cle: str) -> EtapeAnalyse | None:  # pragma: no cover
        ...

    @abstractmethod
    def invalider_etapes_suivantes(self, projet_id: int, ordre: int) -> None:  # pragma: no cover
        ...


class ServiceAnalyseProjet:
    def __init__(
        self,
        projets: DepotProjets,
        analyses: DepotAnalyse,
        albert: AdaptateurAlbert,
    ) -> None:
        self._projets = projets
        self._analyses = analyses
        self._albert = albert

    def configuration(self, projet_id: int) -> ConfigurationAnalyse:
        projet = self._projets.obtenir(projet_id)
        if not projet:
            raise EtapeAbsente
        blocs = self._analyses.lister_blocs_projet(projet_id)
        if not self._analyses.configuration_existe(projet_id):
            defaults = self._analyses.lister_blocs_produit(projet.produit_id)
            blocs = [
                BlocPrompt(
                    cle,
                    libelle,
                    self._contexte(cle, projet, defaults),
                    ordre,
                )
                for ordre, (cle, libelle) in enumerate(BLOCS, 1)
            ]
            blocs = self._analyses.enregistrer_configuration(projet_id, blocs)
        etapes = self._analyses.initialiser_etapes(projet_id)
        return ConfigurationAnalyse(blocs, etapes)

    def enregistrer_configuration(
        self, projet_id: int, contenus: dict[str, str]
    ) -> ConfigurationAnalyse:
        configuration = self.configuration(projet_id)
        blocs = [
            bloc._replace(contenu=contenus.get(bloc.cle, bloc.contenu))
            for bloc in configuration.blocs
        ]
        return ConfigurationAnalyse(
            self._analyses.enregistrer_configuration(projet_id, blocs),
            configuration.etapes,
        )

    def generer(self, projet_id: int, cle: str) -> EtapeAnalyse:
        definition = next((etape for etape in ETAPES if etape[0] == cle), None)
        if not definition:
            raise EtapeAbsente
        configuration = self.configuration(projet_id)
        etape = next(etape for etape in configuration.etapes if etape.cle == cle)
        precedentes = [item for item in configuration.etapes if item.ordre < etape.ordre]
        if precedentes and any(item.valide is None for item in precedentes):
            raise EtapeInaccessible
        entretiens = self._projets.lister_entretiens(projet_id)
        if not entretiens:
            raise ProjetSansEntretien
        prompt = assemble_prompt(configuration.blocs, cle)
        donnees = "\n\n".join(
            f"## {entretien.participant}\n{entretien.contenu}\n{entretien.note_moderateur}"
            for entretien in entretiens
        )
        precedentes_validees = "\n\n".join(
            item.valide for item in precedentes if item.valide is not None
        )
        if precedentes_validees:
            donnees = f"{precedentes_validees}\n\n{donnees}"
        resultat = self._albert.completer(
            [
                {"role": "system", "content": prompt},
                {"role": "user", "content": donnees},
            ],
            temperature=0.3,
        )
        self._analyses.invalider_etapes_suivantes(projet_id, etape.ordre)
        return self._analyses.enregistrer_etape(projet_id, cle, prompt, resultat)

    def modifier(self, projet_id: int, cle: str, contenu: str) -> EtapeAnalyse:
        etape = self._analyses.modifier_etape(projet_id, cle, contenu)
        if not etape:
            raise EtapeAbsente
        return etape

    def valider(self, projet_id: int, cle: str) -> EtapeAnalyse:
        etape = self._analyses.valider_etape(projet_id, cle)
        if not etape:
            raise EtapeAbsente
        return etape

    @staticmethod
    def _contexte(cle: str, projet: object, defaults: list[BlocPrompt]) -> str:
        valeur = next((bloc.contenu for bloc in defaults if bloc.cle == cle), "")
        if cle == "contexte_brief":
            return getattr(projet, "brief")
        if cle == "contexte_projet":
            return f"Projet de recherche : {getattr(projet, 'nom')}"
        return valeur
