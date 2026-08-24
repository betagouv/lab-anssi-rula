from pathlib import Path

from fastapi import APIRouter, Depends

from adaptateurs.albert import AdaptateurAlbertReel
from configuration import charge_configuration
from correspondance.depot import DepotCorrespondance, DepotCorrespondancesCalculees
from correspondance.service import ConfigurationCorrespondance, ServiceCorrespondance
from infra.postgres.depot_correspondance import DepotCorrespondancePostgres
from infra.postgres.depot_correspondances_calculees import DepotCorrespondancesCalculeesPostgres

_prompt_libelle = (Path(__file__).parent.parent / "prompts" / "libelle_cluster.md").read_text()
_prompt_validation = (Path(__file__).parent.parent / "prompts" / "validation_cluster.md").read_text()

routeur = APIRouter()

def _en_dict(clusters: list) -> list[dict]:
    return [{"libelle": c.libelle, "occurrences": c.occurrences, "membres": [m._asdict() for m in c.membres]} for c in clusters]


def fabrique_depot_correspondance() -> DepotCorrespondance:  # pragma: no cover
    return DepotCorrespondancePostgres(charge_configuration().base_de_donnees)


def fabrique_depot_correspondances_calculees() -> DepotCorrespondancesCalculees:  # pragma: no cover
    return DepotCorrespondancesCalculeesPostgres(charge_configuration().base_de_donnees)


def fabrique_service_correspondance(  # pragma: no cover
    depot: DepotCorrespondance = Depends(fabrique_depot_correspondance),
    depot_calcule: DepotCorrespondancesCalculees = Depends(fabrique_depot_correspondances_calculees),
) -> ServiceCorrespondance:
    config = charge_configuration()
    return ServiceCorrespondance(
        depot,
        depot_calcule,
        AdaptateurAlbertReel(config.albert),
        ConfigurationCorrespondance(config.correspondance.seuil, _prompt_libelle, _prompt_validation),
    )


@routeur.get("/correspondances")
def charger(service: ServiceCorrespondance = Depends(fabrique_service_correspondance)) -> list[dict]:
    return _en_dict(service.charger())


@routeur.post("/correspondances/analyser")
def analyser(service: ServiceCorrespondance = Depends(fabrique_service_correspondance)) -> list[dict]:
    return _en_dict(service.analyser())
