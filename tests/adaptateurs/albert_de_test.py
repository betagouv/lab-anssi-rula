from adaptateurs.albert import AdaptateurAlbert


class AdaptateurAlbertDeTest(AdaptateurAlbert):
    def __init__(self) -> None:
        self._reponse = "{}"
        self._reponses: list[str] | None = None
        self._index_reponse = 0
        self._erreur: Exception | None = None
        self.messages_recus: list[list[dict[str, str]]] = []
        self.schemas_recus: list[dict[str, object]] = []

    def avec_reponse(self, reponse: str) -> "AdaptateurAlbertDeTest":
        self._reponse = reponse
        self._reponses = None
        self._index_reponse = 0
        self._erreur = None
        return self

    def avec_reponses(self, reponses: list[str]) -> "AdaptateurAlbertDeTest":
        self._reponses = reponses
        self._index_reponse = 0
        self._erreur = None
        return self

    def avec_erreur(self, erreur: Exception) -> "AdaptateurAlbertDeTest":
        self._erreur = erreur
        self._reponses = None
        return self

    def completer(
        self, messages: list[dict[str, str]], temperature: float = 0.0
    ) -> str:
        self.messages_recus.append(messages)
        if self._erreur:
            raise self._erreur
        if self._reponses is not None:
            reponse = self._reponses[self._index_reponse]
            self._index_reponse += 1
            return reponse
        return self._reponse

    def completer_json(
        self,
        messages: list[dict[str, str]],
        nom_schema: str,
        schema: dict[str, object],
        temperature: float = 0.0,
    ) -> str:
        self.schemas_recus.append(schema)
        return self.completer(messages, temperature)

    def plonger(self, textes: list[str]) -> list[list[float]]:
        return []
