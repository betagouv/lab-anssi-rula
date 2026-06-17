from abc import ABC, abstractmethod

import httpx

from configuration import Albert


class AdaptateurAlbert(ABC):
    @abstractmethod
    def completer(self, messages: list[dict[str, str]], temperature: float = 0.0) -> str: ...


class AdaptateurAlbertReel(AdaptateurAlbert):  # pragma: no cover
    def __init__(self, config: Albert) -> None:
        self._config = config

    def completer(self, messages: list[dict[str, str]], temperature: float = 0.0) -> str:
        with httpx.Client(timeout=120) as client:
            reponse = client.post(
                f"{self._config.url}/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self._config.cle_api}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self._config.modele,
                    "messages": messages,
                    "temperature": temperature,
                },
            )
            reponse.raise_for_status()
            data = reponse.json()
            return data["choices"][0]["message"]["content"]
