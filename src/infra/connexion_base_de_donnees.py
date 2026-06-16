from functools import wraps
from typing import Any, Callable, TypeVar

import psycopg2

F = TypeVar("F", bound=Callable[..., Any])


def avec_connexion(methode: F) -> F:
    @wraps(methode)
    def enveloppe(self: Any, *args: Any, **kwargs: Any) -> Any:
        connexion = psycopg2.connect(
            host=self._config.hote,
            dbname=self._config.nom,
            user=self._config.utilisateur,
            password=self._config.mot_de_passe,
            port=self._config.port,
        )
        connexion.autocommit = True
        self._connexion = connexion
        try:
            return methode(self, *args, **kwargs)
        finally:
            connexion.close()

    return enveloppe  # type: ignore
