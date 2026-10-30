from infra.memoire.depot_termes import DepotListeTermesMemoire
from termes_liste import ServiceListeTermes
from tests.adaptateurs.albert_de_test import AdaptateurAlbertDeTest
from tests.test_transcripts_pdf import _pdf, _reponses_preparation
from transcripts_pdf.service import ServicePreparationTranscript


def test_masque_tous_les_termes_noirs_sans_detection_albert() -> None:
    texte = "Locutrr_01: Paul a rencontré SPEAKER_01 et Paul."
    albert = AdaptateurAlbertDeTest().avec_reponses(
        _reponses_preparation(texte, detections=[])
    )
    liste = DepotListeTermesMemoire()
    service = ServiceListeTermes(liste)
    service.ajouter("Paul")
    service.ajouter("SPEAKER_01")

    preparation = ServicePreparationTranscript(
        albert, "prompt", depot_liste_blanche=DepotListeTermesMemoire()
    ).preparer(
        "synthetique.pdf",
        _pdf(texte),
        "produit",
        "",
        termes_imposes=("Paul", "SPEAKER_01"),
    )

    assert preparation.contenu.startswith("SPEAKER_01:")
    assert preparation.contenu.count("[DONNEE_SENSIBLE_") == 3
    assert all(occurrence.impose for occurrence in preparation.occurrences)
    assert all(
        "Paul" not in occurrence.valeur_anonyme
        for occurrence in preparation.occurrences
    )
    assert all(
        "SPEAKER_01" not in occurrence.valeur_anonyme
        for occurrence in preparation.occurrences
    )
    assert all("Paul" not in repr(schema) for schema in albert.schemas_recus)
    assert all(
        "termes_imposes" not in repr(message) for message in albert.messages_recus
    )


def test_blanc_est_soustrait_avant_union_noire() -> None:
    texte = "Locutrr_01: MSS Pierre est arrivé."
    detections = [("transcript", "MSS Pierre", "identite")]
    albert = AdaptateurAlbertDeTest().avec_reponses(
        _reponses_preparation(texte, detections=detections)
    )
    blancs = DepotListeTermesMemoire()
    ServiceListeTermes(blancs).ajouter("MSS")

    preparation = ServicePreparationTranscript(
        albert, "prompt", depot_liste_blanche=blancs
    ).preparer(
        "synthetique.pdf", _pdf(texte), "produit", "", termes_imposes=("Pierre",)
    )

    assert "MSS" in preparation.contenu
    assert "[DONNEE_SENSIBLE_" in preparation.contenu
    assert "Pierre" not in preparation.contenu


def test_terme_noir_chevauchant_locuteur_masque_le_texte_et_garde_le_prefixe() -> None:
    texte = "Locutrr_01: Secret42 arrive."
    albert = AdaptateurAlbertDeTest().avec_reponses(_reponses_preparation(texte))
    preparation = ServicePreparationTranscript(albert, "prompt").preparer(
        "synthetique.pdf",
        _pdf(texte),
        "produit",
        "",
        termes_imposes=("SPEAKER_01: Secret42",),
    )

    assert preparation.contenu.startswith("SPEAKER_01: ")
    assert "Secret42" not in preparation.contenu
    assert (
        len([occurrence for occurrence in preparation.occurrences if occurrence.impose])
        == 1
    )
