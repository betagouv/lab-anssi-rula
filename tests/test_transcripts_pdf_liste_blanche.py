from pathlib import Path

from infra.memoire.depot_liste_blanche import DepotListeBlancheMemoire
from liste_blanche.service import ServiceListeBlanche
from tests.adaptateurs.albert_de_test import AdaptateurAlbertDeTest
from tests.test_transcripts_pdf import _pdf, _reponses_preparation
from transcripts_pdf.service import ServicePreparationTranscript


def test_filtre_apres_albert_soustrait_les_seeds_et_garde_les_masques_autour() -> None:
    texte = "Locutrr_01: Jean chez MSS accepte LAB42 et Secret42."
    contexte = "Laboratoire d’innovation de l’ANSSI aide Jean chez MSS"
    detections = [
        ("transcript", "Jean chez MSS", "identite"),
        ("transcript", "LAB42", "technologie_ou_produit"),
        ("transcript", "Secret42", "secret"),
        ("contexte", "Laboratoire d’innovation de l’ANSSI", "organisation"),
        ("contexte", "Jean chez MSS", "identite"),
    ]
    albert = AdaptateurAlbertDeTest().avec_reponses(
        _reponses_preparation(texte, contexte, detections)
    )
    depot = DepotListeBlancheMemoire()
    liste = ServiceListeBlanche(depot)
    liste.ajouter("MSS")
    liste.ajouter("LAB")
    liste.ajouter("Laboratoire d’innovation de l’ANSSI")
    liste.ajouter("NE PAS ENVOYER")
    preparation = ServicePreparationTranscript(
        albert, "prompt générique", depot_liste_blanche=depot
    ).preparer("synthetique.pdf", _pdf(texte), "produit", contexte)

    assert "MSS" in preparation.contenu
    assert "[IDENTITE_01]" in preparation.contenu
    assert "[TECHNOLOGIE_OU_PRODUIT_01]" in preparation.contenu
    assert "[SECRET_01]" in preparation.contenu
    assert "Laboratoire d’innovation de l’ANSSI" in preparation.contexte
    valeurs = [occurrence.valeur_originale for occurrence in preparation.occurrences]
    assert valeurs == ["Jean chez", "LAB42", "Secret42", "Jean chez"]
    assert all(
        original[occurrence.debut : occurrence.fin] == occurrence.valeur_originale
        for original, occurrence in [
            (preparation.contenu_original, occurrence)
            if occurrence.champ == "transcript"
            else (preparation.contexte_original, occurrence)
            for occurrence in preparation.occurrences
        ]
    )
    assert all(
        message[0]["content"] == "prompt générique"
        and "NE PAS ENVOYER" not in message[1]["content"]
        for message in albert.messages_recus
    )
    assert "NE PAS ENVOYER" not in repr(albert.schemas_recus)


def test_preparation_sans_depot_ne_change_pas_les_messages_albert() -> None:
    texte = "Locutrr_01: Une donnée sensible."
    reponses = _reponses_preparation(
        texte, detections=[("transcript", "sensible", "donnee_sensible")]
    )
    direct = AdaptateurAlbertDeTest().avec_reponses(reponses)
    avec_liste = AdaptateurAlbertDeTest().avec_reponses(reponses)
    depot = DepotListeBlancheMemoire()
    ServiceListeBlanche(depot).ajouter("MSS")
    pdf = _pdf(texte)
    ServicePreparationTranscript(direct, "prompt générique").preparer(
        "test.pdf", pdf, "produit", ""
    )
    ServicePreparationTranscript(
        avec_liste, "prompt générique", depot_liste_blanche=depot
    ).preparer("test.pdf", pdf, "produit", "")
    assert avec_liste.messages_recus == direct.messages_recus
    assert avec_liste.schemas_recus == direct.schemas_recus


def test_prompt_exclut_les_segments_generiques_isoles_sans_seed() -> None:
    prompt = Path("src/prompts/anonymisation_transcript.md").read_text(encoding="utf-8")
    assert "ponctuation seule" in prompt
    assert "mot grammatical isolé" in prompt
    assert "libellé générique isolé" in prompt
    assert all(
        seed not in prompt
        for seed in (
            "Mon Service Sécurisé",
            "Laboratoire d’innovation de l’ANSSI",
            "Annecy",
        )
    )
