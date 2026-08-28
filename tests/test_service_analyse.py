from datetime import date

import pytest

from projets.analyse import (
    EtapeAbsente,
    EtapeInaccessible,
    ProjetSansEntretien,
    ServiceAnalyseProjet,
    assemble_prompt,
)
from tests.adaptateurs.albert_de_test import AdaptateurAlbertDeTest
from tests.projets.depot_projets_de_test import DepotProjetsDeTest
from infra.memoire.depot_analyse import DepotAnalyseMemoire
from projets.analyse import BlocPrompt


def test_assemble_les_blocs_dans_l_ordre_et_omet_les_vides() -> None:
    blocs = [
        BlocPrompt("instructions_sortie", "Sortie", "sortie", 6),
        BlocPrompt("role", "Rôle", "role", 1),
        BlocPrompt("contexte_produit", "Produit", "produit", 2),
        BlocPrompt("contexte_brief", "Brief", "", 3),
        BlocPrompt("contexte_projet", "Projet", "projet", 4),
        BlocPrompt("regles", "Règles", "règles", 5),
        BlocPrompt("consigne_scan-neutre", "Consigne", "consigne", 7),
    ]

    assert assemble_prompt(blocs, "scan-neutre") == "\n\n".join(
        ("role", "produit", "projet", "règles", "consigne", "sortie")
    )


def test_configuration_copie_les_defauts_et_injecte_le_contexte_du_projet() -> None:
    projets = DepotProjetsDeTest()
    projet = projets.ajouter(1, "Recherche", "Brief")
    analyse = DepotAnalyseMemoire(
        {1: [BlocPrompt("role", "Le rôle", "Rôle par défaut", 1)]}
    )

    configuration = ServiceAnalyseProjet(
        projets, analyse, AdaptateurAlbertDeTest()
    ).configuration(projet.id)

    contenus = {bloc.cle: bloc.contenu for bloc in configuration.blocs}
    assert contenus["role"] == "Rôle par défaut"
    assert contenus["contexte_brief"] == "Brief"
    assert contenus["contexte_projet"] == "Projet de recherche : Recherche"
    modifiee = ServiceAnalyseProjet(
        projets, analyse, AdaptateurAlbertDeTest()
    ).enregistrer_configuration(projet.id, {"role": "Rôle personnalisé"})
    assert (
        next(bloc for bloc in modifiee.blocs if bloc.cle == "role").contenu
        == "Rôle personnalisé"
    )


def test_generation_exige_la_validation_de_l_etape_precedente() -> None:
    projets = DepotProjetsDeTest()
    projet = projets.ajouter(1, "Recherche", "")
    projets.ajouter_entretien(projet.id, "A", date(2026, 8, 25), "B", "Transcript", "")
    albert = AdaptateurAlbertDeTest().avec_reponse("Résultat")
    service = ServiceAnalyseProjet(projets, DepotAnalyseMemoire(), albert)

    service.generer(projet.id, "scan-neutre")
    assert (
        service.modifier(projet.id, "scan-neutre", "Brouillon").brouillon == "Brouillon"
    )
    with pytest.raises(EtapeInaccessible):
        service.generer(projet.id, "points-a-retenir")

    service.valider(projet.id, "scan-neutre")
    assert service.generer(projet.id, "points-a-retenir").brouillon == "Résultat"


def test_refuse_projet_et_etape_inconnus_ou_sans_entretien() -> None:
    projets = DepotProjetsDeTest()
    analyse = DepotAnalyseMemoire()
    service = ServiceAnalyseProjet(projets, analyse, AdaptateurAlbertDeTest())

    with pytest.raises(EtapeAbsente):
        service.configuration(1)
    projet = projets.ajouter(1, "Recherche", "")
    with pytest.raises(EtapeAbsente):
        service.generer(projet.id, "inconnue")
    with pytest.raises(ProjetSansEntretien):
        service.generer(projet.id, "scan-neutre")
    with pytest.raises(EtapeAbsente):
        service.modifier(projet.id, "inconnue", "texte")
    with pytest.raises(EtapeAbsente):
        service.valider(projet.id, "inconnue")


def test_depot_memoire_gere_les_etapes_vides_et_une_configuration_existante() -> None:
    depot = DepotAnalyseMemoire()
    bloc = BlocPrompt("role", "Rôle", "texte", 1)
    assert depot.enregistrer_configuration(1, [bloc]) == [bloc]
    assert depot.enregistrer_configuration(1, [bloc]) == [bloc]
    assert depot.configuration_existe(1)
    depot.initialiser_etapes(1)
    assert depot.modifier_etape(1, "scan-neutre", "texte") is not None
    assert depot.modifier_etape(1, "inconnue", "texte") is None
    assert depot.valider_etape(1, "inconnue") is None
    assert depot.valider_etape(1, "scan-neutre") is not None


def test_configuration_vide_reste_vide_apres_sauvegarde() -> None:
    projets = DepotProjetsDeTest()
    projet = projets.ajouter(1, "Recherche", "")
    depot = DepotAnalyseMemoire()
    depot.enregistrer_configuration(1, [])
    assert depot.configuration_existe(1)
    assert (
        ServiceAnalyseProjet(projets, depot, AdaptateurAlbertDeTest())
        .configuration(projet.id)
        .blocs
        == []
    )
