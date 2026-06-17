from abc import ABC, abstractmethod
from typing import NamedTuple

import httpx

from configuration import FeatureBase


class IdeeBrute(NamedTuple):
    id_externe: str
    titre: str
    nb_votes: int


class AdaptateurFeatureBase(ABC):
    @abstractmethod
    def lister_idees(self) -> list[IdeeBrute]: ...


class AdaptateurFeatureBaseReel(AdaptateurFeatureBase):  # pragma: no cover
    def __init__(self, config: FeatureBase) -> None:
        self._config = config

    def lister_idees(self) -> list[IdeeBrute]:
        if not self._config.cle_api:
            raise ValueError("FEATUREBASE_CLE_API non configurée")
        base = self._config.api_url.rstrip("/")
        headers = {"Authorization": f"Bearer {self._config.cle_api}"}
        with httpx.Client(timeout=30) as client:
            board_id = self._trouver_board_id(client, headers, base)
            return self._lister_posts(client, headers, base, board_id)

    def _trouver_board_id(self, client: httpx.Client, headers: dict[str, str], base: str) -> str:
        r = client.get(f"{base}/boards", headers=headers)
        r.raise_for_status()
        boards = r.json().get("data", r.json())
        for board in boards:
            if board.get("name") == self._config.board_name:
                return board["id"]
        raise ValueError(f"Board introuvable : {self._config.board_name!r}")

    def _lister_posts(self, client: httpx.Client, headers: dict[str, str], base: str, board_id: str) -> list[IdeeBrute]:
        idees: list[IdeeBrute] = []
        cursor: str | None = None
        while True:
            params: dict[str, str | int] = {"boardId": board_id, "sortBy": "upvotes", "limit": 100}
            if cursor:
                params["cursor"] = cursor
            r = client.get(f"{base}/posts", headers=headers, params=params)
            r.raise_for_status()
            data = r.json()
            for post in data.get("data", []):
                idees.append(IdeeBrute(id_externe=post["id"], titre=post["title"], nb_votes=post.get("upvotes", 0)))
            cursor = data.get("nextCursor")
            if not cursor:
                break
        return idees
