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


def base_de_donnees_est_disponible(config: Any) -> bool:
    try:
        with psycopg2.connect(
            host=config.hote,
            dbname=config.nom,
            user=config.utilisateur,
            password=config.mot_de_passe,
            port=config.port,
            connect_timeout=5,
        ) as connexion:
            with connexion.cursor() as curseur:
                curseur.execute("SELECT 1")
        return True
    except psycopg2.Error:
        return False
