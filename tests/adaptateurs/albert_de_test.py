from adaptateurs.albert import AdaptateurAlbert


class AdaptateurAlbertDeTest(AdaptateurAlbert):
    def __init__(self) -> None:
        self._reponse = "{}"
        self.messages_recus: list[list[dict[str, str]]] = []

    def avec_reponse(self, reponse: str) -> "AdaptateurAlbertDeTest":
        self._reponse = reponse
        return self

    def completer(self, messages: list[dict[str, str]]) -> str:
        self.messages_recus.append(messages)
        return self._reponse
