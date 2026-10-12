import httpx
import json
import pytest

from adaptateurs.albert import (
    AdaptateurAlbert,
    CompletionTranscript,
    DELAI_MAXIMUM_ALBERT,
    _lire_evenement_flux,
    _lire_reponse_completion,
    _lire_reponse_completion_transcript,
    _metriques_reponse_transcript,
    _traduit_erreur,
)
from adaptateurs.exceptions import (
    DelaiAlbertDepasse,
    ErreurCommunicationAlbert,
    ErreurHTTPAlbert,
    ReponseAlbertInvalide,
)
from tests.adaptateurs.albert_de_test import AdaptateurAlbertDeTest


@pytest.mark.parametrize(
    ("erreur", "type_attendu"),
    [
        (httpx.ReadTimeout("délai dépassé"), DelaiAlbertDepasse),
        (httpx.ConnectError("réseau indisponible"), ErreurCommunicationAlbert),
        (
            httpx.HTTPStatusError(
                "erreur HTTP",
                request=httpx.Request("POST", "https://albert.test"),
                response=httpx.Response(
                    503,
                    request=httpx.Request("POST", "https://albert.test"),
                ),
            ),
            ErreurHTTPAlbert,
        ),
    ],
)
def test_traduit_les_erreurs_albert(
    erreur: httpx.HTTPError, type_attendu: type
) -> None:
    assert isinstance(_traduit_erreur(erreur), type_attendu)


def test_timeout_albert_est_limite_a_trente_secondes() -> None:
    assert DELAI_MAXIMUM_ALBERT == 30


def test_lit_les_fragments_sse_sans_retourner_les_raisons():
    evenement = json.dumps(
        {
            "choices": [
                {
                    "delta": {"reasoning": "secret", "content": '{"ok":'},
                    "finish_reason": None,
                }
            ]
        }
    )
    assert _lire_evenement_flux(evenement) == ('{"ok":', False, None, None, 6)
    assert _lire_evenement_flux(
        json.dumps(
            {
                "choices": [{"delta": {}, "finish_reason": "stop"}],
                "usage": {"completion_tokens": 12},
            }
        )
    ) == ("", False, "stop", 12, 0)
    assert _lire_evenement_flux(
        json.dumps({"choices": [], "usage": {"completion_tokens": 12}})
    ) == ("", False, None, 12, 0)
    assert _lire_evenement_flux("[DONE]") == ("", True, None, None, 0)


def test_refuse_un_evenement_sse_invalide():
    with pytest.raises(ReponseAlbertInvalide):
        _lire_evenement_flux("pas-json")
    with pytest.raises(ReponseAlbertInvalide):
        _lire_evenement_flux(
            json.dumps({"choices": [{"delta": {"content": ["invalide"]}}]})
        )
    with pytest.raises(ReponseAlbertInvalide):
        _lire_evenement_flux(
            json.dumps({"choices": [{"delta": {"reasoning": ["invalide"]}}]})
        )


def test_refuse_une_reponse_completion_tronquee():
    with pytest.raises(ReponseAlbertInvalide):
        _lire_reponse_completion(
            {"choices": [{"finish_reason": "length", "message": {"content": None}}]}
        )


def test_metriques_reponse_transcript_ne_contiennent_pas_le_contenu() -> None:
    metriques = _metriques_reponse_transcript(
        {
            "choices": [
                {
                    "finish_reason": "stop",
                    "message": {
                        "content": "TEXTE_PRIVE",
                        "reasoning": "RAISONNEMENT_PRIVE",
                    },
                }
            ]
        }
    )

    assert metriques["finish_reason"] == "stop"
    assert metriques["contenu_caracteres"] == len("TEXTE_PRIVE")
    assert metriques["raisonnement_caracteres"] == len("RAISONNEMENT_PRIVE")
    assert "TEXTE_PRIVE" not in str(metriques)
    assert "RAISONNEMENT_PRIVE" not in str(metriques)


def test_lit_une_reponse_completion_terminee():
    assert (
        _lire_reponse_completion(
            {"choices": [{"finish_reason": "stop", "message": {"content": "{}"}}]}
        )
        == "{}"
    )


def test_completion_transcript_conserve_le_diagnostic_sur_une_chaine() -> None:
    resultat = CompletionTranscript("{}", {"finish_reason": "stop"})

    assert resultat == "{}"
    assert resultat.diagnostic == {"finish_reason": "stop"}


def test_completion_transcript_de_base_reutilise_la_completion_json() -> None:
    albert = AdaptateurAlbertDeTest().avec_reponse("{}")

    assert (
        AdaptateurAlbert.completer_json_raisonnement_transcript(
            albert,
            [], "schema", {}, "high", 0.5, 0.75
        )
        == "{}"
    )


def test_transcript_refuse_une_reponse_non_terminee_ou_vide():
    for choix in (
        {"finish_reason": "length", "message": {"content": "{}"}},
        {"finish_reason": "stop", "message": {"content": ""}},
        {"finish_reason": "tool_calls", "message": {"content": None}},
    ):
        with pytest.raises(ReponseAlbertInvalide):
            _lire_reponse_completion_transcript({"choices": [choix]})


def test_transcript_lit_une_reponse_stop_non_vide():
    assert (
        _lire_reponse_completion_transcript(
            {"choices": [{"finish_reason": "stop", "message": {"content": "{}"}}]}
        )
        == "{}"
    )
