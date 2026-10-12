import json

import pytest

from tests.adaptateurs.albert_de_test import AdaptateurAlbertDeTest
from transcripts_pdf.analyse import ServiceAnalysePdf, _contenu_tour


def test_analyse_produit_verifie_les_verbatims_et_tours() -> None:
    reponse: dict[str, object] = {
        "resume": "Le participant décrit un besoin d’export.",
        "themes": ["Export"],
        "highlights": [
            {
                "type": "besoin",
                "description": "Exporter les données.",
                "sentiment": "neutre",
                "gravite": None,
                "verbatim": "Je veux exporter.",
                "tour_id": 1,
                "speaker_id": "SPEAKER_01",
            }
        ],
        "fonctionnalites": [
            {
                "action": "Exporter les données",
                "verbatim": "Je veux exporter.",
                "tour_id": 1,
                "speaker_id": "SPEAKER_01",
            }
        ],
    }
    albert = AdaptateurAlbertDeTest().avec_reponse(json.dumps(reponse))
    service = ServiceAnalysePdf(
        albert,
        {"produit": "prompt", "bizdev": "prompt"},
    )

    resultat = service.analyser(
        "produit", "SPEAKER_01: Je veux exporter.", "", [], "pdf-v1"
    )

    assert resultat.fonctionnalites[0]["verbatim"] == "Je veux exporter."
    tours = json.loads(albert.messages_recus[0][1]["content"].split("TOURS:\n", 1)[1])
    assert tours == [
        {"tour_id": 1, "speaker_id": "SPEAKER_01", "contenu": "Je veux exporter."}
    ]


def test_analyse_refuse_un_verbatim_absent_du_tour_reference() -> None:
    reponse = {
        "resume": "Résumé.",
        "themes": [],
        "highlights": [
            {
                "type": "besoin",
                "description": "Besoin.",
                "sentiment": "neutre",
                "gravite": None,
                "verbatim": "Texte absent.",
                "tour_id": 1,
                "speaker_id": "SPEAKER_01",
            }
        ],
        "fonctionnalites": [],
    }
    service = ServiceAnalysePdf(
        AdaptateurAlbertDeTest().avec_reponse(json.dumps(reponse)),
        {"produit": "prompt", "bizdev": "prompt"},
    )

    with pytest.raises(ValueError, match="ne correspond pas"):
        service.analyser("produit", "SPEAKER_01: Texte présent.", "", [], "pdf-v1")


def test_analyse_bizdev_exige_une_reference_sur_chaque_extraction() -> None:
    reponse: dict[str, object] = {
        "resume": "Résumé.",
        "themes": [],
        **{
            cle: []
            for cle in (
                "enjeux",
                "besoins_globaux",
                "freins",
                "motivations",
                "opportunites",
                "propositions",
                "signaux_positifs",
                "suites_evoquees",
            )
        },
        "fonctionnalites": [],
    }
    reponse["freins"] = [{"description": "Prix"}]
    service = ServiceAnalysePdf(
        AdaptateurAlbertDeTest().avec_reponse(json.dumps(reponse)),
        {"produit": "prompt", "bizdev": "prompt"},
    )

    with pytest.raises(ValueError, match="Extraction BizDev"):
        service.analyser("bizdev", "SPEAKER_01: Le prix est élevé.", "", [], "pdf-v1")


@pytest.mark.parametrize(
    "reponse",
    [
        "pas-json",
        "{}",
        '{"resume":3,"themes":[],"highlights":[],"fonctionnalites":[]}',
        '{"resume":"x","themes":"x","highlights":[],"fonctionnalites":[]}',
        '{"resume":"x","themes":[],"highlights":"x","fonctionnalites":[]}',
        '{"resume":"x","themes":[],"highlights":[],"fonctionnalites":[{"action":3}]}',
        '{"resume":"x","themes":[],"highlights":[],"fonctionnalites":[{"action":"exporter","verbatim":"Texte","tour_id":"1","speaker_id":"SPEAKER_01"}]}',
        '{"resume":"x","themes":[],"highlights":[{}],"fonctionnalites":[]}',
    ],
)
def test_analyse_refuse_un_schema_invalide(reponse: str) -> None:
    service = ServiceAnalysePdf(
        AdaptateurAlbertDeTest().avec_reponse(reponse),
        {"produit": "prompt", "bizdev": "prompt"},
    )

    with pytest.raises(ValueError):
        service.analyser("produit", "SPEAKER_01: Texte", "", [], "pdf-v1")


def test_reference_hors_transcript_a_un_contenu_vide() -> None:
    assert _contenu_tour("SPEAKER_01: Texte", 2) == ""
