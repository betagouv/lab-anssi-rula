from api.listes import creer_routeur_liste
from configuration import charge_configuration
from infra.postgres.depot_termes import DepotListeTermesPostgres
from termes_liste import ServiceListeTermes


def fabrique_service_liste_noire() -> ServiceListeTermes:
    return ServiceListeTermes(
        DepotListeTermesPostgres(charge_configuration().base_de_donnees, "noire")
    )


routeur = creer_routeur_liste("noire", fabrique_service_liste_noire)
