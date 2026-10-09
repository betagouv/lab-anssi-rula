import os
from pathlib import Path
import subprocess
import sys

from configuration import (
    Albert,
    BaseDeDonnees,
    Configuration,
    Correspondance,
    Rula,
    charge_configuration,
    _valider_parallelisme_anonymisation,
)


def test_valeurs_par_defaut():
    config = charge_configuration()
    assert config.rula.port == 3001
    assert config.rula.max_requetes_par_minute == 100
    assert config.albert.modele == "openweight-medium"
    assert config.albert.modele_embeddings == "BAAI/bge-m3"
    assert config.albert.max_completion_tokens_transcripts == 16384
    assert config.albert.temperature_transcripts == 1.0
    assert config.albert.top_p_transcripts == 1.0
    assert config.albert.parallelisme_anonymisation == 8
    assert config.base_de_donnees.port == 5432
    assert config.base_de_donnees.nom == "rula"
    assert config.correspondance.seuil == 0.35


def test_configuration_des_parametres_echantillonnage_transcripts(monkeypatch):
    monkeypatch.setenv("ALBERT_TEMPERATURE_TRANSCRIPTS", "0.8")
    monkeypatch.setenv("ALBERT_TOP_P_TRANSCRIPTS", "0.9")

    config = charge_configuration()

    assert config.albert.temperature_transcripts == 0.8
    assert config.albert.top_p_transcripts == 0.9


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


def test_configuration_refuse_un_parallelisme_non_positif():
    import pytest

    with pytest.raises(ValueError, match="doit être positif"):
        _valider_parallelisme_anonymisation(0)


def test_configuration_charge_parallelisme_depuis_lenvironnement():
    code = (
        "from configuration import charge_configuration; "
        "print(charge_configuration().albert.parallelisme_anonymisation)"
    )
    resultat = subprocess.run(
        [sys.executable, "-c", code],
        cwd=Path(__file__).resolve().parents[1],
        env={
            **os.environ,
            "ALBERT_PARALLELISME_ANONYMISATION": "3",
            "PYTHONPATH": str(Path(__file__).resolve().parents[1] / "src"),
        },
        capture_output=True,
        check=True,
        text=True,
    )
    assert resultat.stdout.strip() == "3"
