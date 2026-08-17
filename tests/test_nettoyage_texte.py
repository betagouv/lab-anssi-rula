from nettoyage_texte import nettoie_texte


def test_nettoie_texte_remplace_les_controles_des_exports() -> None:
    assert nettoie_texte("c\x19est \x1cimportant\x1d") == "c’est «important»"


def test_nettoie_texte_conserve_les_retours_a_la_ligne() -> None:
    assert nettoie_texte("ligne 1\nligne 2\tfin") == "ligne 1\nligne 2\tfin"
