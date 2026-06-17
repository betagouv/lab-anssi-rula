from abc import ABC, abstractmethod
from typing import NamedTuple

import httpx

from configuration import FeatureBase

_BASE_URL = "https://do.featurebase.app/v2"


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
        headers = {"Authorization": f"Bearer {self._config.cle_api}"}
        with httpx.Client(timeout=30) as client:
            board_id = self._trouver_board_id(client, headers)
            return self._lister_posts(client, headers, board_id)

    def _trouver_board_id(self, client: httpx.Client, headers: dict[str, str]) -> str:
        r = client.get(f"{_BASE_URL}/boards", headers=headers)
        r.raise_for_status()
        boards = r.json().get("data", r.json())
        for board in boards:
            if board.get("name") == self._config.board_name:
                return board["id"]
        raise ValueError(f"Board introuvable : {self._config.board_name!r}")

    def _lister_posts(self, client: httpx.Client, headers: dict[str, str], board_id: str) -> list[IdeeBrute]:
        idees: list[IdeeBrute] = []
        cursor: str | None = None
        while True:
            params: dict[str, str | int] = {"boardId": board_id, "sortBy": "upvotes", "limit": 100}
            if cursor:
                params["cursor"] = cursor
            r = client.get(f"{_BASE_URL}/posts", headers=headers, params=params)
            r.raise_for_status()
            data = r.json()
            for post in data.get("data", []):
                idees.append(IdeeBrute(id_externe=post["id"], titre=post["title"], nb_votes=post.get("upvotes", 0)))
            cursor = data.get("nextCursor")
            if not cursor:
                break
        return idees
