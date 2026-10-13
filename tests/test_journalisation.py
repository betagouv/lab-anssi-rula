import logging

import pytest

from journalisation import FiltreSuiviPreparation, installe_filtre_suivi_preparation


@pytest.mark.parametrize(
    ("methode", "chemin", "statut", "conserve"),
    [
        (
            "GET",
            "/api/transcripts-pdf/preparation/0123456789abcdef0123456789abcdef",
            200,
            False,
        ),
        (
            "POST",
            "/api/transcripts-pdf/preparation/0123456789abcdef0123456789abcdef",
            200,
            True,
        ),
        (
            "GET",
            "/api/transcripts-pdf/preparation/0123456789abcdef0123456789abcdef",
            404,
            True,
        ),
        (
            "GET",
            "/api/transcripts-pdf/preparation/0123456789abcdef0123456789abcdef",
            429,
            True,
        ),
        (
            "GET",
            "/api/transcripts-pdf/preparation/0123456789abcdef0123456789abcdef",
            500,
            True,
        ),
        ("GET", "/api/transcripts-pdf/preparation/autre", 200, True),
        ("GET", "/api/transcripts-pdf/123", 200, True),
        (
            "GET",
            "/api/transcripts-pdf/preparation/0123456789abcdef0123456789abcdef?x=1",
            200,
            True,
        ),
    ],
)
def test_filtre_suivi_preparation(methode, chemin, statut, conserve) -> None:
    record = logging.LogRecord(
        "uvicorn.access",
        logging.INFO,
        "",
        0,
        "%s",
        ("127.0.0.1", methode, chemin, "1.1", statut),
        None,
    )

    assert FiltreSuiviPreparation().filter(record) is conserve


def test_filtre_suivi_preparation_conserve_les_records_hors_format_uvicorn() -> None:
    record = logging.LogRecord("uvicorn.access", logging.INFO, "", 0, "%s", (), None)

    assert FiltreSuiviPreparation().filter(record)


def test_installe_filtre_suivi_preparation_une_seule_fois() -> None:
    journal = logging.getLogger("uvicorn.access")
    nombre_initial = sum(
        isinstance(filtre, FiltreSuiviPreparation) for filtre in journal.filters
    )

    installe_filtre_suivi_preparation()
    installe_filtre_suivi_preparation()

    assert sum(
        isinstance(filtre, FiltreSuiviPreparation) for filtre in journal.filters
    ) == max(1, nombre_initial)
