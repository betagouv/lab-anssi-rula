import unicodedata

import pytest

from infra.memoire.depot_liste_blanche import DepotListeBlancheMemoire
from liste_blanche.depot import RevisionObsolete, TermeDejaPresent
from liste_blanche.service import ServiceListeBlanche, normaliser_terme
from transcripts_pdf.protection_liste_blanche import (
    normaliser_pour_comparaison,
    positions_liste_blanche,
    soustraire_intervalle,
)


def test_normalisation_trim_compresse_nfc_et_casefold() -> None:
    libelle, cle = normaliser_terme("  Mon\u00a0  Service Se\u0301curise\u0301  ")
    assert libelle == "Mon Service Sécurisé"
    assert cle == "mon service sécurisé"
    assert unicodedata.is_normalized("NFC", libelle)
    with pytest.raises(ValueError):
        normaliser_terme("   .!?_   ")
    with pytest.raises(ValueError):
        normaliser_terme("x" * 121)


def test_service_depot_refuse_cle_dupliquee_et_revision_obsolete() -> None:
    depot = DepotListeBlancheMemoire()
    service = ServiceListeBlanche(depot)
    terme = service.ajouter("Mon terme")
    with pytest.raises(TermeDejaPresent):
        service.ajouter(" MON   TERME ")
    modifie = service.modifier(terme.id, "Autre terme", terme.revision)
    assert modifie.revision == 2
    with pytest.raises(RevisionObsolete):
        service.modifier(terme.id, "Conflit", terme.revision)
    with pytest.raises(RevisionObsolete):
        service.supprimer(terme.id, terme.revision)
    service.supprimer(terme.id, modifie.revision)
    assert service.lister() == []


@pytest.mark.parametrize(
    ("texte", "terme", "attendu"),
    [
        ("collaboration (LAB), LAB42 mon_lab LAB!", "LAB", [(15, 18), (35, 38)]),
        ("Straße STRASSE", "strasse", [(0, 6), (7, 14)]),
        (
            "E\u0301quipe Sécurisé Securise",
            "ÉQUIPE",
            [(0, 7)],
        ),
        (
            "Laboratoire d’innovation\u00a0 de\n l’ANSSI.",
            "laboratoire d'innovation de l'anssi",
            [(0, 37)],
        ),
    ],
)
def test_matching_unicode_frontieres_et_offsets_originaux(
    texte: str, terme: str, attendu: list[tuple[int, int]]
) -> None:
    assert positions_liste_blanche(texte, [terme]) == attendu


def test_matching_nfc_et_nfd_coreen_preserve_les_offsets() -> None:
    assert positions_liste_blanche("가", ["가"]) == [(0, 2)]
    assert positions_liste_blanche("가", ["가"]) == [(0, 1)]
    assert positions_liste_blanche("각", ["각"]) == [(0, 3)]
    assert positions_liste_blanche("각", ["각"]) == [(0, 2)]
    assert positions_liste_blanche("각", ["각"]) == [(0, 1)]


def test_casefold_n_est_pas_un_accent_insensible_et_ne_coupe_pas_une_expansion() -> (
    None
):
    assert positions_liste_blanche("Sécurisé", ["Securise"]) == []
    assert positions_liste_blanche("ß", ["s"]) == []
    assert positions_liste_blanche("ß", ["ss"]) == [(0, 1)]
    assert normaliser_pour_comparaison("Laboratoire d’innovation") == (
        "laboratoire d'innovation"
    )


def test_soustraction_sans_chevauchement_preserve_la_ponctuation_du_masque() -> None:
    texte = "-a!"
    assert soustraire_intervalle(texte, 0, len(texte), []) == [(0, 3)]


def test_soustraction_preserve_les_symboles_du_residu_sensitive() -> None:
    texte = "!Pass-42! MSS"
    protection = positions_liste_blanche(texte, ["MSS"])
    restants = soustraire_intervalle(texte, 0, len(texte), protection)
    assert [texte[debut:fin] for debut, fin in restants] == ["!Pass-42!"]


def test_soustraction_preserve_la_partie_sensible_et_supprime_les_residus() -> None:
    texte = "Jean chez MSS / Projet-secret !!!"
    protection = positions_liste_blanche(texte, ["MSS"])
    masque = (0, len(texte))
    restants = soustraire_intervalle(texte, *masque, protection)
    assert [texte[debut:fin] for debut, fin in restants] == [
        "Jean chez",
        "/ Projet-secret !!!",
    ]
