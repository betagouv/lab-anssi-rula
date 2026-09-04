from abc import ABC, abstractmethod

import httpx

from configuration import Albert
from adaptateurs.exceptions import (
    DelaiAlbertDepasse,
    ErreurAlbert,
    ErreurCommunicationAlbert,
    ErreurHTTPAlbert,
    ReponseAlbertInvalide,
)


DELAI_MAXIMUM_ALBERT = 30


def _traduit_erreur(erreur: httpx.HTTPError) -> ErreurAlbert:
    if isinstance(erreur, httpx.TimeoutException):
        return DelaiAlbertDepasse()
    if isinstance(erreur, httpx.HTTPStatusError):
        return ErreurHTTPAlbert()
    return ErreurCommunicationAlbert()


class AdaptateurAlbert(ABC):
    @abstractmethod
    def completer(
        self, messages: list[dict[str, str]], temperature: float = 0.0
    ) -> str: ...

    def completer_json(
        self,
        messages: list[dict[str, str]],
        nom_schema: str,
        schema: dict[str, object],
        temperature: float = 0.0,
    ) -> str:
        return self.completer(messages, temperature)

    @abstractmethod
    def plonger(self, textes: list[str]) -> list[list[float]]: ...


class AdaptateurAlbertReel(AdaptateurAlbert):  # pragma: no cover
    def __init__(self, config: Albert) -> None:
        self._config = config

    def completer(
        self, messages: list[dict[str, str]], temperature: float = 0.0
    ) -> str:
        return self._completer(messages, temperature)

    def completer_json(
        self,
        messages: list[dict[str, str]],
        nom_schema: str,
        schema: dict[str, object],
        temperature: float = 0.0,
    ) -> str:
        return self._completer(
            messages,
            temperature,
            {
                "type": "json_schema",
                "json_schema": {
                    "name": nom_schema,
                    "strict": True,
                    "schema": schema,
                },
            },
        )

    def _completer(
        self,
        messages: list[dict[str, str]],
        temperature: float,
        response_format: dict[str, object] | None = None,
    ) -> str:
        try:
            with httpx.Client(timeout=DELAI_MAXIMUM_ALBERT) as client:
                corps: dict[str, object] = {
                    "model": self._config.modele,
                    "messages": messages,
                    "temperature": temperature,
                }
                if response_format:
                    corps["response_format"] = response_format
                reponse = client.post(
                    f"{self._config.url}/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self._config.cle_api}",
                        "Content-Type": "application/json",
                    },
                    json=corps,
                )
                reponse.raise_for_status()
        except httpx.HTTPError as erreur:
            raise _traduit_erreur(erreur) from erreur
        try:
            data = reponse.json()
            return data["choices"][0]["message"]["content"]
        except (ValueError, KeyError, IndexError, TypeError) as erreur:
            raise ReponseAlbertInvalide from erreur

    def plonger(self, textes: list[str]) -> list[list[float]]:
        vecteurs: list[list[float]] = []
        try:
            with httpx.Client(timeout=DELAI_MAXIMUM_ALBERT) as client:
                for debut in range(0, len(textes), 32):
                    reponse = client.post(
                        f"{self._config.url}/v1/embeddings",
                        headers={
                            "Authorization": f"Bearer {self._config.cle_api}",
                            "Content-Type": "application/json",
                        },
                        json={
                            "model": self._config.modele_embeddings,
                            "input": textes[debut : debut + 32],
                        },
                    )
                    reponse.raise_for_status()
                    try:
                        vecteurs.extend(d["embedding"] for d in reponse.json()["data"])
                    except (ValueError, KeyError, IndexError, TypeError) as erreur:
                        raise ReponseAlbertInvalide from erreur
        except httpx.HTTPError as erreur:
            raise _traduit_erreur(erreur) from erreur
        return vecteurs
