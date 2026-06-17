import os
from typing import NamedTuple


class Albert(NamedTuple):
    url: str
    cle_api: str
    modele: str


class BaseDeDonnees(NamedTuple):
    hote: str
    port: int
    nom: str
    utilisateur: str
    mot_de_passe: str


class Rula(NamedTuple):
    port: int
    hote: str
    max_requetes_par_minute: int


class FeatureBase(NamedTuple):
    cle_api: str
    board_name: str
    api_url: str


class Configuration(NamedTuple):
    rula: Rula
    albert: Albert
    base_de_donnees: BaseDeDonnees
    featurebase: FeatureBase


def charge_configuration() -> Configuration:
    return Configuration(
        rula=Rula(
            port=int(os.environ.get("RULA_PORT", "3001")),
            hote=os.environ.get("RULA_HOTE", "localhost"),
            max_requetes_par_minute=int(os.environ.get("RULA_MAX_REQUETES_PAR_MINUTE", "100")),
        ),
        albert=Albert(
            url=os.environ.get("ALBERT_URL", ""),
            cle_api=os.environ.get("ALBERT_CLE_API", ""),
            modele=os.environ.get("ALBERT_MODELE", "openweight-medium"),
        ),
        base_de_donnees=BaseDeDonnees(
            hote=os.environ.get("DB_HOTE", "localhost"),
            port=int(os.environ.get("DB_PORT", "5432")),
            nom=os.environ.get("DB_NOM", "rula"),
            utilisateur=os.environ.get("DB_UTILISATEUR", "rula"),
            mot_de_passe=os.environ.get("DB_MOT_DE_PASSE", ""),
        ),
        featurebase=FeatureBase(
            cle_api=os.environ.get("FEATUREBASE_CLE_API", ""),
            board_name=os.environ.get("FEATUREBASE_BOARD_NAME", ""),
            api_url=os.environ.get("FEATUREBASE_API_URL", "https://do.featurebase.app/v2"),
        ),
    )
