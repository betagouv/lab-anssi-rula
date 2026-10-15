import json
from typing import Any, cast

import pytest

from tests.adaptateurs.albert_de_test import AdaptateurAlbertDeTest
from transcripts_pdf.analyse import (
    ErreurValidationAnalyse,
    ServiceAnalysePdf,
    _contenu_tour,
)


def _reference(tour_id: int, debut: int, fin: int) -> dict[str, dict[str, int]]:
    return {"reference": {"tour_id": tour_id, "token_debut": debut, "token_fin": fin}}


def _produit(**valeurs: object) -> dict[str, object]:
    return {
        "contexte": {
            "produit": "Portail",
            "profil_utilisateur": "Agent",
            "objectif": "Comprendre l’export",
        },
        "ouverture": "L’agent veut exporter les données.",
        "points_cles": ["L’export est demandé."],
        "profil": [],
        "sujets": [],
        "pistes": [],
        "prochaines_etapes": [],
        "fonctionnalites": [],
        **valeurs,
    }


def test_analyse_produit_verifie_les_verbatims_et_tours() -> None:
    reponse = _produit(
        sujets=[
            {
                "titre": "Export",
                "constat": "L’agent veut exporter.",
                "enseignements": [
                    {"description": "La personne demande l’export.", "nature": "fait", **_reference(1, 0, 2)}
                ],
            }
        ],
        fonctionnalites=[{"action": "Exporter les données", **_reference(1, 0, 2)}],
    )
    albert = AdaptateurAlbertDeTest().avec_reponse(json.dumps(reponse))
    service = ServiceAnalysePdf(
        albert,
        {"produit": "prompt", "bizdev": "prompt"},
        {"temperature": 1.0, "top_p": 1.0},
    )

    resultat = service.analyser(
        "produit", "SPEAKER_01: Je veux exporter.", "", [], "produit-v1"
    )

    assert resultat.fonctionnalites[0]["verbatim"] == "Je veux exporter."
    assert (
        cast(list[dict[str, Any]], resultat.contenu["sujets"])[0]["enseignements"][0][
            "verbatim"
        ]
        == "Je veux exporter."
    )
    tours = json.loads(albert.messages_recus[0][1]["content"].split("TOURS:\n", 1)[1])
    assert tours == [
        {
            "tour_id": 1,
            "speaker_id": "SPEAKER_01",
            "token_max": 2,
            "tokens": [
                [0, "Je"],
                [1, "veux"],
                [2, "exporter."],
            ],
        }
    ]
    assert '"enum": [1]' in json.dumps(albert.schemas_recus[0])
    branche = cast(Any, albert.schemas_recus[0])["$defs"]["reference"]["anyOf"][0]
    assert branche["properties"]["token_fin"]["maximum"] == 2
    assert albert.parametres_transcript == [(1.0, 1.0, "medium")]
    assert albert.efforts_recus == ["medium"]


def test_pistes_analytiques_ne_deviennent_pas_des_fonctionnalites() -> None:
    reponse = _produit(
        sujets=[
            {
                "titre": "Recherche",
                "constat": "L’agent hésite.",
                "enseignements": [
                    {"description": "La personne décrit trois écrans successifs.", "nature": "fait", **_reference(1, 0, 4)},
                    {
                        "description": "La navigation peut contribuer à l’hésitation.",
                        "nature": "hypothese",
                        **_reference(1, 0, 4),
                    },
                    {
                        "description": "Une recherche unifiée mérite une étude.",
                        "nature": "interpretation",
                        **_reference(1, 0, 4),
                    },
                ],
            }
        ],
        pistes=[
            {
                "action": "Étudier une recherche unifiée",
                "besoin": "Trouver plus vite",
                "origine": "proposition_analyste",
                "effort_estime": "Non estimé",
                **_reference(1, 0, 2),
            }
        ],
        fonctionnalites=[
            {"action": "Mesurer automatiquement", **_reference(1, 0, 4)}
        ],
    )
    service = ServiceAnalysePdf(
        AdaptateurAlbertDeTest().avec_reponse(json.dumps(reponse)),
        {"produit": "prompt", "bizdev": "prompt"},
    )

    resultat = service.analyser(
        "produit", "SPEAKER_01: Je change trois fois d’écran.", "", [], "produit-v1"
    )

    assert resultat.fonctionnalites[0]["action"] == "Mesurer automatiquement"
    assert [
        e["nature"]
        for e in cast(list[dict[str, Any]], resultat.contenu["sujets"])[0][
            "enseignements"
        ]
    ] == ["fait", "hypothese", "interpretation"]
    assert (
        cast(list[dict[str, Any]], resultat.contenu["pistes"])[0]["effort_estime"]
        == "Non estimé"
    )


def test_analyse_refuse_un_verbatim_absent_du_tour_reference() -> None:
    reponse = _produit(
        sujets=[
            {
                "titre": "Sujet",
                "constat": "Constat.",
                "enseignements": [
                    {"description": "Le passage n’est pas disponible.", "nature": "fait", **_reference(1, 2, 2)}
                ],
            }
        ]
    )
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


def test_analyse_bizdev_reconstruit_chaque_citation_depuis_les_tokens() -> None:
    categories = (
        "enjeux",
        "besoins_globaux",
        "freins",
        "motivations",
        "opportunites",
        "propositions",
        "signaux_positifs",
        "suites_evoquees",
    )
    reference = {
        "description": "Fait.",
        **_reference(2, 0, 1),
    }
    reponse = {
        "resume": "Résumé.",
        "themes": [],
        **{cle: [reference.copy()] for cle in categories},
        "fonctionnalites": [{"action": "Confirmer", **_reference(1, 0, 4)}],
    }
    service = ServiceAnalysePdf(
        AdaptateurAlbertDeTest().avec_reponse(json.dumps(reponse)),
        {"produit": "prompt", "bizdev": "prompt"},
    )

    resultat = service.analyser(
        "bizdev",
        "SPEAKER_01: L’utilisateur veut « exporter ».\nSPEAKER_01: Oui, demain.",
        "",
        [],
        "pdf-v1",
    )

    assert all(
        cast(list[dict[str, object]], resultat.contenu[cle])[0]
        == {
            "description": "Fait.",
            "tour_id": 2,
            "verbatim": "Oui, demain.",
            "speaker_id": "SPEAKER_01",
        }
        for cle in categories
    )
    assert resultat.fonctionnalites == [
        {
            "action": "Confirmer",
            "tour_id": 1,
            "verbatim": "L’utilisateur veut « exporter ».",
            "speaker_id": "SPEAKER_01",
        }
    ]
    assert all(
        "reference" not in item
        for elements in resultat.contenu.values()
        if isinstance(elements, list)
        for item in elements
        if isinstance(item, dict)
    )


@pytest.mark.parametrize(
    ("tour_id", "token_debut", "token_fin"),
    [(2, 0, 0), (1, True, 0), (1, 2, 1), (1, 0, 99)],
)
def test_analyse_refuse_les_positions_de_reference_invalides(
    tour_id: int, token_debut: int, token_fin: int
) -> None:
    reponse = _produit(
        fonctionnalites=[
            {
                "action": "Exporter",
                "reference": {
                    "tour_id": tour_id,
                    "token_debut": token_debut,
                    "token_fin": token_fin,
                },
            }
        ]
    )
    service = ServiceAnalysePdf(
        AdaptateurAlbertDeTest().avec_reponse(json.dumps(reponse)),
        {"produit": "prompt", "bizdev": "prompt"},
    )

    with pytest.raises(ValueError):
        service.analyser("produit", "SPEAKER_01: Texte.", "", [], "pdf-v1")


def test_analyse_refuse_une_fin_qui_depasse_token_max_du_tour() -> None:
    reponse = _produit(fonctionnalites=[{"action": "Exporter", **_reference(1, 0, 72)}])
    albert = AdaptateurAlbertDeTest().avec_reponse(json.dumps(reponse))
    service = ServiceAnalysePdf(albert, {"produit": "prompt", "bizdev": "prompt"})

    with pytest.raises(ValueError):
        service.analyser(
            "produit", "SPEAKER_01: " + " ".join(["mot"] * 71), "", [], "pdf-v1"
        )

    branche = cast(Any, albert.schemas_recus[0])["$defs"]["reference"]["anyOf"][0]
    assert branche["properties"]["token_fin"]["maximum"] == 70


def test_analyse_refuse_un_transcript_sans_tour_citable() -> None:
    albert = AdaptateurAlbertDeTest()
    service = ServiceAnalysePdf(
        albert,
        {"produit": "prompt", "bizdev": "prompt"},
    )

    with pytest.raises(ErreurValidationAnalyse) as erreur:
        service.analyser("produit", "Texte sans locuteur.", "", [], "pdf-v1")

    assert erreur.value.code == "aucun_tour_citable"
    assert albert.schemas_recus == []


@pytest.mark.parametrize(
    "reponse",
    [
        "pas-json",
        "{}",
        '{"contexte":{},"ouverture":"x","profil":[],"sujets":[],"pistes":[],"prochaines_etapes":[],"fonctionnalites":[]}',
        '{"contexte":{"produit":3,"profil_utilisateur":"x","objectif":"x"},"ouverture":"x","profil":[],"sujets":[],"pistes":[],"prochaines_etapes":[],"fonctionnalites":[]}',
        '{"contexte":{"produit":"x","profil_utilisateur":"x","objectif":"x"},"ouverture":"x","points_cles":[],"profil":[],"sujets":[{"titre":"x","constat":"x","enseignements":[{"description":"x","nature":"recommandation","reference":{"tour_id":1,"token_debut":0,"token_fin":0}}]}],"pistes":[],"prochaines_etapes":[],"fonctionnalites":[]}',
        '{"contexte":{"produit":"x","profil_utilisateur":"x","objectif":"x"},"ouverture":"x","points_cles":[],"profil":[],"sujets":[{"titre":"x","constat":"x","enseignements":[{"description":"x","nature":[],"reference":{"tour_id":1,"token_debut":0,"token_fin":0}}]}],"pistes":[],"prochaines_etapes":[],"fonctionnalites":[]}',
        '{"contexte":{"produit":"x","profil_utilisateur":"x","objectif":"x"},"ouverture":"x","profil":[],"sujets":[],"pistes":[{"action":"x","besoin":"x","origine":"x","effort_estime":"x"}],"prochaines_etapes":[],"fonctionnalites":[]}',
        '{"contexte":{"produit":"x","profil_utilisateur":"x","objectif":"x"},"ouverture":"x","points_cles":[],"profil":[],"sujets":[],"pistes":[],"prochaines_etapes":[],"fonctionnalites":[{"action":"exporter","reference":{"tour_id":"1","token_debut":0,"token_fin":0}}]}',
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
