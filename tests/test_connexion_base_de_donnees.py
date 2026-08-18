import psycopg2

from configuration import BaseDeDonnees
from infra import connexion_base_de_donnees


class _Curseur:
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return None

    def execute(self, requete):
        self.requete = requete


class _Connexion:
    def __init__(self):
        self.curseur = _Curseur()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return None

    def cursor(self):
        return self.curseur


def test_base_de_donnees_est_disponible(monkeypatch):
    connexion = _Connexion()
    appels = []
    monkeypatch.setattr(
        connexion_base_de_donnees.psycopg2,
        "connect",
        lambda **kwargs: appels.append(kwargs) or connexion,
    )

    disponible = connexion_base_de_donnees.base_de_donnees_est_disponible(
        BaseDeDonnees("hote", 5432, "nom", "utilisateur", "mot-de-passe")
    )

    assert disponible is True
    assert appels == [
        {
            "host": "hote",
            "dbname": "nom",
            "user": "utilisateur",
            "password": "mot-de-passe",
            "port": 5432,
            "connect_timeout": 5,
        }
    ]
    assert connexion.curseur.requete == "SELECT 1"


def test_base_de_donnees_indisponible(monkeypatch):
    monkeypatch.setattr(
        connexion_base_de_donnees.psycopg2,
        "connect",
        lambda **kwargs: (_ for _ in ()).throw(psycopg2.OperationalError()),
    )

    disponible = connexion_base_de_donnees.base_de_donnees_est_disponible(
        BaseDeDonnees("hote", 5432, "nom", "utilisateur", "mot-de-passe")
    )

    assert disponible is False
