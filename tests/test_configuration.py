from configuration import (
    Albert,
    BaseDeDonnees,
    Configuration,
    Correspondance,
    Rula,
    charge_configuration,
)


def test_valeurs_par_defaut():
    config = charge_configuration()
    assert config.rula.port == 3001
    assert config.rula.max_requetes_par_minute == 100
    assert config.albert.modele == "openweight-medium"
    assert config.albert.modele_embeddings == "BAAI/bge-m3"
    assert config.base_de_donnees.port == 5432
    assert config.base_de_donnees.nom == "rula"
    assert config.correspondance.seuil == 0.35


def test_configuration_constructible_avec_valeurs_custom():
    config = Configuration(
        rula=Rula(port=4000, hote="custom", max_requetes_par_minute=50),
        albert=Albert(
            url="https://albert.example.com",
            cle_api="ma-cle",
            modele="openweight-large",
            modele_embeddings="bge",
        ),
        base_de_donnees=BaseDeDonnees(
            hote="db", port=5433, nom="test", utilisateur="u", mot_de_passe="s"
        ),
        correspondance=Correspondance(seuil=0.5),
    )
    assert config.rula.port == 4000
    assert config.albert.cle_api == "ma-cle"
    assert config.base_de_donnees.nom == "test"
    assert config.correspondance.seuil == 0.5


def test_configuration_accepte_les_variables_postgresql_clever_cloud(monkeypatch):
    for nom in ("DB_HOTE", "DB_PORT", "DB_NOM", "DB_UTILISATEUR", "DB_MOT_DE_PASSE"):
        monkeypatch.delenv(nom, raising=False)
    monkeypatch.setenv("POSTGRESQL_ADDON_HOST", "postgres.clever-cloud.com")
    monkeypatch.setenv("POSTGRESQL_ADDON_PORT", "5433")
    monkeypatch.setenv("POSTGRESQL_ADDON_DB", "rula-demo")
    monkeypatch.setenv("POSTGRESQL_ADDON_USER", "rula")
    monkeypatch.setenv("POSTGRESQL_ADDON_PASSWORD", "mot-de-passe")

    config = charge_configuration()

    assert config.base_de_donnees == BaseDeDonnees(
        hote="postgres.clever-cloud.com",
        port=5433,
        nom="rula-demo",
        utilisateur="rula",
        mot_de_passe="mot-de-passe",
    )
