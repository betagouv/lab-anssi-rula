from pathlib import Path
import subprocess
import sys

from configuration import charge_configuration


def test_configuration_conserve_les_reglages_utiles_a_la_pseudonymisation() -> None:
    configuration = charge_configuration()
    assert configuration.albert.modele == "openweight-medium"
    assert configuration.albert.parallelisme_anonymisation == 8
    assert configuration.albert.delai_preparation_transcripts == 180
    assert configuration.base_de_donnees.nom == "rula"


def test_configuration_lit_les_delais_et_le_parallelisme_depuis_lenvironnement() -> (
    None
):
    racine = Path(__file__).resolve().parents[1]
    resultat = subprocess.run(
        [
            sys.executable,
            "-c",
            "from configuration import charge_configuration; c=charge_configuration().albert; print(c.parallelisme_anonymisation, c.delai_preparation_transcripts)",
        ],
        cwd=racine,
        env={
            **__import__("os").environ,
            "PYTHONPATH": str(racine / "src"),
            "ALBERT_PARALLELISME_ANONYMISATION": "3",
            "ALBERT_DELAI_PREPARATION_TRANSCRIPTS": "420",
        },
        capture_output=True,
        check=True,
        text=True,
    )
    assert resultat.stdout.strip() == "3 420"
