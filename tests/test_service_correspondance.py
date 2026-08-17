from adaptateurs.albert import AdaptateurAlbert
from correspondance.depot import Cluster, Membre
from correspondance.service import ServiceCorrespondance
from infra.memoire.depot_correspondance import DepotCorrespondanceMemoire
from infra.memoire.depot_correspondances_calculees import DepotCorrespondancesCalculeesMemoire


class _AlbertJsonInvalideDeTest(AdaptateurAlbert):
    def completer(self, messages: list[dict[str, str]], temperature: float = 0.0) -> str:
        return "réponse non JSON"

    def plonger(self, textes: list[str]) -> list[list[float]]:
        return []


def test_valider_garde_cluster_si_json_invalide() -> None:
    membres = [Membre("idee", "Feature A", None, None), Membre("idee", "Feature B", None, None)]
    cluster = Cluster(libelle="test", occurrences=2, membres=membres)
    service = ServiceCorrespondance(
        DepotCorrespondanceMemoire([]),
        DepotCorrespondancesCalculeesMemoire(),
        _AlbertJsonInvalideDeTest(),
        0.35,
        "prompt libelle",
        "prompt validation",
    )
    assert service._valider([cluster]) == [cluster]


def test_nommer_donne_un_libelle_aux_groupes_unitaires() -> None:
    membre = Membre("idee", "Actualiser le référentiel de mesures", None, None)
    cluster = Cluster(libelle="", occurrences=1, membres=[membre])
    service = ServiceCorrespondance(
        DepotCorrespondanceMemoire([]),
        DepotCorrespondancesCalculeesMemoire(),
        _AlbertJsonInvalideDeTest(),
        0.35,
        "prompt libelle",
        "prompt validation",
    )

    assert service._nommer([cluster]) == [
        Cluster(libelle="Actualiser le référentiel de mesures", occurrences=1, membres=[membre])
    ]
