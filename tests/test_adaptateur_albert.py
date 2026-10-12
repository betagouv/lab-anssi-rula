import httpx
import json
import pytest

from adaptateurs.albert import (
    DELAI_MAXIMUM_ALBERT,
    _lire_evenement_flux,
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
    assert _lire_evenement_flux(evenement) == ('{"ok":', False, None, None)
    assert _lire_evenement_flux(
        json.dumps(
            {
                "choices": [{"delta": {}, "finish_reason": "stop"}],
                "usage": {"completion_tokens": 12},
            }
        )
    ) == ("", False, "stop", 12)
    assert _lire_evenement_flux(
        json.dumps({"choices": [], "usage": {"completion_tokens": 12}})
    ) == ("", False, None, 12)
    assert _lire_evenement_flux("[DONE]") == ("", True, None, None)


def test_refuse_un_evenement_sse_invalide():
    with pytest.raises(ReponseAlbertInvalide):
        _lire_evenement_flux("pas-json")
    with pytest.raises(ReponseAlbertInvalide):
        _lire_evenement_flux(
            json.dumps({"choices": [{"delta": {"content": ["invalide"]}}]})
        )
