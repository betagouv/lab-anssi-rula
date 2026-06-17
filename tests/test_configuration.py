from configuration import Albert, BaseDeDonnees, Configuration, FeatureBase, Rula, charge_configuration


def test_valeurs_par_defaut():
    config = charge_configuration()
    assert config.rula.port == 3001
    assert config.rula.max_requetes_par_minute == 100
    assert config.albert.modele == "openweight-medium"
    assert config.base_de_donnees.port == 5432
    assert config.base_de_donnees.nom == "rula"


def test_configuration_constructible_avec_valeurs_custom():
    config = Configuration(
        rula=Rula(port=4000, hote="custom", max_requetes_par_minute=50),
        albert=Albert(url="https://albert.example.com", cle_api="ma-cle", modele="openweight-large"),
        base_de_donnees=BaseDeDonnees(hote="db", port=5433, nom="test", utilisateur="u", mot_de_passe="s"),
        featurebase=FeatureBase(cle_api="fb-cle", board_name="Mon Board"),
    )
    assert config.rula.port == 4000
    assert config.albert.cle_api == "ma-cle"
    assert config.base_de_donnees.nom == "test"
    assert config.featurebase.board_name == "Mon Board"
