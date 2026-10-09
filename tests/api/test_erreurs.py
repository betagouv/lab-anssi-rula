from api.erreurs import detail_erreur_validation


def test_validation_sans_emplacement_affiche_un_libelle_generique() -> None:
    resultat = detail_erreur_validation([{"type": "missing"}])

    assert resultat["champs"] == [
        "Le renseignement concernant le champ saisi est obligatoire."
    ]
