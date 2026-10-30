from api.listes import creer_routeur_liste
from configuration import charge_configuration
from infra.postgres.depot_termes import DepotListeTermesPostgres
from termes_liste import ServiceListeTermes


def fabrique_service_liste_blanche() -> ServiceListeTermes:
    return ServiceListeTermes(
        DepotListeTermesPostgres(charge_configuration().base_de_donnees, "blanche")
    )


routeur = creer_routeur_liste("blanche", fabrique_service_liste_blanche)
