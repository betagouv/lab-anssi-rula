import httpx
import pytest

from adaptateurs.albert import DELAI_MAXIMUM_ALBERT, _traduit_erreur
from adaptateurs.exceptions import (
    DelaiAlbertDepasse,
    ErreurCommunicationAlbert,
    ErreurHTTPAlbert,
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
