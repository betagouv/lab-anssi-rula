import httpx
import json
import pytest

from adaptateurs.albert import (
    DELAI_MAXIMUM_ALBERT,
    _lire_evenement_flux,
    _lire_reponse_completion,
    _lire_reponse_completion_transcript,
    _traduit_erreur,
)
from adaptateurs.exceptions import (
    DelaiAlbertDepasse,
    ErreurCommunicationAlbert,
    ErreurHTTPAlbert,
    ReponseAlbertInvalide,
)


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


def test_lit_une_reponse_completion_terminee():
    assert (
        _lire_reponse_completion(
            {"choices": [{"finish_reason": "stop", "message": {"content": "{}"}}]}
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
