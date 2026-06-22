from abc import ABC, abstractmethod

import httpx

from configuration import Albert


class AdaptateurAlbert(ABC):
    @abstractmethod
    def completer(self, messages: list[dict[str, str]], temperature: float = 0.0) -> str: ...

    @abstractmethod
    def plonger(self, textes: list[str]) -> list[list[float]]: ...


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

    def plonger(self, textes: list[str]) -> list[list[float]]:
        vecteurs: list[list[float]] = []
        with httpx.Client(timeout=120) as client:
            for debut in range(0, len(textes), 32):
                reponse = client.post(
                    f"{self._config.url}/v1/embeddings",
                    headers={
                        "Authorization": f"Bearer {self._config.cle_api}",
                        "Content-Type": "application/json",
                    },
                    json={"model": self._config.modele_embeddings, "input": textes[debut : debut + 32]},
                )
                reponse.raise_for_status()
                vecteurs.extend(d["embedding"] for d in reponse.json()["data"])
        return vecteurs
