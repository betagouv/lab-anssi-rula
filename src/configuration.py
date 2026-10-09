import os
from typing import NamedTuple


class Albert(NamedTuple):
    url: str
    cle_api: str
    modele: str
    modele_embeddings: str
    delai_transcripts: int = 180
    max_completion_tokens_transcripts: int = 16384
    temperature_transcripts: float = 1.0
    top_p_transcripts: float = 1.0


class Correspondance(NamedTuple):
    seuil: float


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


class Configuration(NamedTuple):
    rula: Rula
    albert: Albert
    base_de_donnees: BaseDeDonnees
    correspondance: Correspondance


def _variable(nom: str, defaut: str, *noms_secours: str) -> str:
    for candidat in (nom, *noms_secours):
        valeur = os.environ.get(candidat)
        if valeur:
            return valeur
    return defaut


def charge_configuration() -> Configuration:
    return Configuration(
        rula=Rula(
            port=int(os.environ.get("RULA_PORT", "3001")),
            hote=os.environ.get("RULA_HOTE", "localhost"),
            max_requetes_par_minute=int(
                os.environ.get("RULA_MAX_REQUETES_PAR_MINUTE", "100")
            ),
        ),
        albert=Albert(
            url=os.environ.get("ALBERT_URL", ""),
            cle_api=os.environ.get("ALBERT_CLE_API", ""),
            modele=os.environ.get("ALBERT_MODELE", "openweight-medium"),
            modele_embeddings=os.environ.get("ALBERT_MODELE_EMBEDDINGS", "BAAI/bge-m3"),
            delai_transcripts=int(os.environ.get("ALBERT_DELAI_TRANSCRIPTS", "180")),
            max_completion_tokens_transcripts=int(
                os.environ.get("ALBERT_MAX_COMPLETION_TOKENS_TRANSCRIPTS", "16384")
            ),
            temperature_transcripts=float(
                os.environ.get("ALBERT_TEMPERATURE_TRANSCRIPTS", "1.0")
            ),
            top_p_transcripts=float(os.environ.get("ALBERT_TOP_P_TRANSCRIPTS", "1.0")),
        ),
        base_de_donnees=BaseDeDonnees(
            hote=_variable("DB_HOTE", "localhost", "POSTGRESQL_ADDON_HOST"),
            port=int(_variable("DB_PORT", "5432", "POSTGRESQL_ADDON_PORT")),
            nom=_variable("DB_NOM", "rula", "POSTGRESQL_ADDON_DB"),
            utilisateur=_variable("DB_UTILISATEUR", "rula", "POSTGRESQL_ADDON_USER"),
            mot_de_passe=_variable("DB_MOT_DE_PASSE", "", "POSTGRESQL_ADDON_PASSWORD"),
        ),
        correspondance=Correspondance(
            seuil=float(os.environ.get("CORRESPONDANCE_SEUIL", "0.35")),
        ),
    )
