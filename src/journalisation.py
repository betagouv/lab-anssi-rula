import logging
import re


class FiltreSuiviPreparation(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if not isinstance(record.args, tuple) or len(record.args) != 5:
            return True
        _, methode, chemin, _, statut = record.args
        return not (
            methode == "GET"
            and isinstance(chemin, str)
            and re.fullmatch(r"/api/transcripts-pdf/preparation/[0-9a-f]{32}", chemin)
            and str(statut) == "200"
        )


def installe_filtre_suivi_preparation() -> None:
    journal = logging.getLogger("uvicorn.access")
    if not any(
        isinstance(filtre, FiltreSuiviPreparation) for filtre in journal.filters
    ):
        journal.addFilter(FiltreSuiviPreparation())
