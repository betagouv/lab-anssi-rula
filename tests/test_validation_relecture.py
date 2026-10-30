import pytest

from transcripts_pdf.validation_relecture import (
    verifier_etat_relecture,
    verifier_projection_finale,
)


def _etat(debut: int, fin: int, valeur_anonyme: str = "[MASQUE]") -> dict:
    return {
        "masques": [
            {
                "identifiant": "masque-1",
                "categorie": "donnee_sensible",
                "valeur_anonyme": valeur_anonyme,
                "actif": True,
            }
        ],
        "plages": [
            {
                "identifiant": "plage-1",
                "masque_identifiant": "masque-1",
                "champ": "transcript",
                "debut": debut,
                "fin": fin,
            }
        ],
        "annulations": [],
        "retablissements": [],
    }


def test_convertit_les_offsets_utf16_et_valide_la_projection() -> None:
    assert verifier_etat_relecture(
        "😀 Secret",
        "",
        [],
        ("Secret",),
        _etat(3, 9),
    ) == ("😀 [MASQUE]", "")


@pytest.mark.parametrize(
    ("etat", "termes"),
    [
        (_etat(1, 3), ("Secret",)),
        (_etat(3, 9, "Secret"), ("Secret",)),
        (_etat(3, 9, "[Secret]"), ("Secret",)),
    ],
)
def test_refuse_plage_invalide_ou_terme_reintroduit(
    etat: dict, termes: tuple[str, ...]
) -> None:
    with pytest.raises(ValueError):
        verifier_etat_relecture("😀 Secret", "", [], termes, etat)


def test_tous_les_etats_annules_et_retablis_doivent_couvrir_le_terme() -> None:
    etat = _etat(3, 9)
    etat["annulations"] = [{"masques": [], "plages": []}]
    with pytest.raises(ValueError):
        verifier_etat_relecture("😀 Secret", "", [], ("Secret",), etat)


def test_validation_finale_preserve_le_prefixe_locuteur_et_bloque_le_texte() -> None:
    with pytest.raises(ValueError):
        verifier_projection_finale(
            "SPEAKER_01: Secret42", "", ("SPEAKER_01: Secret42",)
        )
    verifier_projection_finale(
        "SPEAKER_01: [DONNEE_SENSIBLE_01]", "", ("SPEAKER_01: Secret42",)
    )
