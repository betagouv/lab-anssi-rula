from abc import ABC, abstractmethod
import asyncio
import json
import time
from typing import Any

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


def _lire_evenement_flux(
    donnees: str,
) -> tuple[str, bool, str | None, int | None, int]:
    if donnees == "[DONE]":
        return "", True, None, None, 0
    try:
        evenement = json.loads(donnees)
        choix = evenement.get("choices", [{}])
        choix = choix[0] if choix else {}
        contenu = choix.get("delta", {}).get("content") or ""
        raisonnement = choix.get("delta", {}).get("reasoning") or ""
        raison = choix.get("finish_reason")
        tokens = evenement.get("usage", {}).get("completion_tokens")
        if not isinstance(contenu, str) or (
            raison is not None and not isinstance(raison, str)
        ):
            raise TypeError
        if not isinstance(raisonnement, str):
            raise TypeError
        return (
            contenu,
            False,
            raison,
            tokens if isinstance(tokens, int) else None,
            len(raisonnement),
        )
    except (ValueError, KeyError, IndexError, TypeError, AttributeError) as erreur:
        raise ReponseAlbertInvalide from erreur


def _traduit_erreur(erreur: httpx.HTTPError) -> ErreurAlbert:
    if isinstance(erreur, httpx.TimeoutException):
        return DelaiAlbertDepasse()
    if isinstance(erreur, httpx.HTTPStatusError):
        return ErreurHTTPAlbert()
    return ErreurCommunicationAlbert()


def _metriques_reponse_transcript(donnees: Any) -> dict[str, str | int | float | None]:
    choix = donnees.get("choices") if isinstance(donnees, dict) else None
    premier = choix[0] if isinstance(choix, list) and choix else None
    message = premier.get("message") if isinstance(premier, dict) else None
    contenu = message.get("content") if isinstance(message, dict) else None
    raisonnement = (
        message.get("reasoning_content", message.get("reasoning"))
        if isinstance(message, dict)
        else None
    )
    fin = premier.get("finish_reason") if isinstance(premier, dict) else None
    return {
        "choix_nombre": len(choix) if isinstance(choix, list) else 0,
        "message_champs_nombre": len(message) if isinstance(message, dict) else 0,
        "finish_reason": fin
        if isinstance(fin, str)
        and fin in {"stop", "length", "tool_calls", "content_filter"}
        else "autre"
        if isinstance(fin, str)
        else None,
        "contenu_type": type(contenu).__name__ if contenu is not None else "absent",
        "contenu_caracteres": len(contenu) if isinstance(contenu, str) else 0,
        "raisonnement_type": type(raisonnement).__name__
        if raisonnement is not None
        else "absent",
        "raisonnement_caracteres": len(raisonnement)
        if isinstance(raisonnement, str)
        else 0,
        "refus_present": int(
            isinstance(message, dict) and bool(message.get("refusal"))
        ),
    }


class CompletionTranscript(str):
    diagnostic: dict[str, str | int | float | None]

    def __new__(
        cls,
        contenu: str,
        diagnostic: dict[str, str | int | float | None],
    ) -> "CompletionTranscript":
        instance = super().__new__(cls, contenu)
        instance.diagnostic = diagnostic
        return instance


def _lire_reponse_completion(data: Any) -> str:
    try:
        choix = data["choices"][0]
        contenu = choix["message"]["content"]
        if choix.get("finish_reason") == "length" or not isinstance(contenu, str):
            raise TypeError
        return contenu
    except (ValueError, KeyError, IndexError, TypeError) as erreur:
        raise ReponseAlbertInvalide from erreur


def _lire_reponse_completion_transcript(data: Any) -> str:
    try:
        choix = data["choices"][0]
        contenu = choix["message"]["content"]
        if (
            choix.get("finish_reason") != "stop"
            or not isinstance(contenu, str)
            or not contenu
        ):
            raise TypeError
        return contenu
    except (ValueError, KeyError, IndexError, TypeError) as erreur:
        raise ReponseAlbertInvalide from erreur


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

    def completer_json_raisonnement(
        self,
        messages: list[dict[str, str]],
        nom_schema: str,
        schema: dict[str, object],
        effort: str,
        temperature: float = 0.0,
    ) -> str:
        return self.completer_json(messages, nom_schema, schema, temperature)

    def completer_json_raisonnement_preparation(
        self,
        messages: list[dict[str, str]],
        nom_schema: str,
        schema: dict[str, object],
        effort: str,
        temperature: float = 0.0,
    ) -> str:
        return self.completer_json_raisonnement(
            messages,
            nom_schema,
            schema,
            effort,
            0.0 if temperature is None else temperature,
        )

    def completer_json_raisonnement_transcript(
        self,
        messages: list[dict[str, str]],
        nom_schema: str,
        schema: dict[str, object],
        effort: str,
        temperature: float = 0.0,
        top_p: float | None = None,
    ) -> str:
        return self.completer_json_raisonnement(
            messages,
            nom_schema,
            schema,
            effort,
            temperature,
        )

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

    def completer_json_raisonnement(
        self,
        messages: list[dict[str, str]],
        nom_schema: str,
        schema: dict[str, object],
        effort: str,
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
            effort,
            self._config.delai_transcripts,
            self._config.max_completion_tokens_transcripts,
        )

    def completer_json_raisonnement_preparation(
        self,
        messages: list[dict[str, str]],
        nom_schema: str,
        schema: dict[str, object],
        effort: str,
        temperature: float | None = None,
    ) -> str:
        debut = time.monotonic()
        metriques: dict[str, int | float | str | None] = {
            "modele": self._config.modele,
            "budget_completion": self._config.max_completion_tokens_transcripts,
            "statut_http": None,
            "delai_entetes_s": None,
            "premier_contenu_s": None,
            "duree_totale_s": None,
            "evenements": 0,
            "completion_tokens": None,
            "raisonnement_caracteres": 0,
            "contenu_caracteres": 0,
            "finish_reason": None,
            "request_id": None,
            "tentatives": 0,
            "retry_cause_type": None,
        }
        self.metriques_dernier_flux = metriques

        async def consommer(debut_tentative: float) -> str:
            contenu: list[str] = []
            termine = False
            async with httpx.AsyncClient(
                timeout=self._config.delai_transcripts
            ) as client:
                async with client.stream(
                    "POST",
                    f"{self._config.url}/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self._config.cle_api}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self._config.modele,
                        "messages": messages,
                        "temperature": (
                            self._config.temperature_transcripts
                            if temperature is None
                            else temperature
                        ),
                        "top_p": self._config.top_p_transcripts,
                        "response_format": {
                            "type": "json_schema",
                            "json_schema": {
                                "name": nom_schema,
                                "strict": True,
                                "schema": schema,
                            },
                        },
                        "reasoning_effort": effort,
                        "max_completion_tokens": self._config.max_completion_tokens_transcripts,
                        "stream": True,
                    },
                ) as reponse:
                    metriques["statut_http"] = reponse.status_code
                    metriques["request_id"] = reponse.headers.get("x-request-id")
                    metriques["delai_entetes_s"] = round(
                        time.monotonic() - debut_tentative, 3
                    )
                    reponse.raise_for_status()
                    async for ligne in reponse.aiter_lines():
                        if not ligne.startswith("data:"):
                            continue
                        metriques["evenements"] = int(metriques["evenements"] or 0) + 1
                        fragment, fin, raison, tokens, caracteres_raisonnement = (
                            _lire_evenement_flux(ligne[5:].strip())
                        )
                        metriques["raisonnement_caracteres"] = (
                            int(metriques["raisonnement_caracteres"] or 0)
                            + caracteres_raisonnement
                        )
                        if fragment:
                            metriques["contenu_caracteres"] = int(
                                metriques["contenu_caracteres"] or 0
                            ) + len(fragment)
                            if metriques["premier_contenu_s"] is None:
                                metriques["premier_contenu_s"] = round(
                                    time.monotonic() - debut_tentative, 3
                                )
                            contenu.append(fragment)
                        if fin:
                            termine = True
                        if raison:
                            metriques["finish_reason"] = raison
                        if tokens is not None:
                            metriques["completion_tokens"] = tokens
            if not termine or metriques["finish_reason"] != "stop" or not contenu:
                raise ReponseAlbertInvalide
            return "".join(contenu)

        tentatives = 0
        cause_retry = None
        try:
            while True:
                debut_tentative = time.monotonic()
                metriques.update(
                    statut_http=None,
                    delai_entetes_s=None,
                    premier_contenu_s=None,
                    evenements=0,
                    completion_tokens=None,
                    raisonnement_caracteres=0,
                    contenu_caracteres=0,
                    finish_reason=None,
                    request_id=None,
                    duree_tentative_s=None,
                )
                tentatives += 1
                metriques.update(
                    tentatives=tentatives,
                    retry_cause_type=cause_retry,
                    delai_tentative_s=self._config.delai_preparation_transcripts,
                )
                try:
                    return asyncio.run(
                        asyncio.wait_for(
                            consommer(debut_tentative),
                            self._config.delai_preparation_transcripts,
                        )
                    )
                except TimeoutError as erreur:
                    delai = DelaiAlbertDepasse()
                    delai.diagnostic.update(
                        groupe=None,
                        delai_tentative_s=self._config.delai_preparation_transcripts,
                        duree_tentative_s=round(
                            time.monotonic() - debut_tentative, 3
                        ),
                        duree_totale_s=round(time.monotonic() - debut, 3),
                        tentatives=tentatives,
                        retry_cause_type=cause_retry,
                    )
                    raise delai from erreur
                except httpx.HTTPError as erreur:
                    if (
                        isinstance(erreur, httpx.HTTPStatusError)
                        and erreur.response is not None
                    ):
                        metriques["statut_http"] = erreur.response.status_code
                    if tentatives == 1 and isinstance(
                        erreur,
                        (
                            httpx.RemoteProtocolError,
                            httpx.ReadError,
                            httpx.ConnectError,
                        ),
                    ):
                        cause_retry = type(erreur).__name__
                        continue
                    erreur_traduite = _traduit_erreur(erreur)
                    if isinstance(erreur_traduite, DelaiAlbertDepasse):
                        erreur_traduite.diagnostic.update(
                            groupe=None,
                            delai_tentative_s=self._config.delai_preparation_transcripts,
                            duree_tentative_s=round(
                                time.monotonic() - debut_tentative, 3
                            ),
                            duree_totale_s=round(time.monotonic() - debut, 3),
                            tentatives=tentatives,
                            retry_cause_type=cause_retry,
                        )
                    raise erreur_traduite from erreur
                finally:
                    metriques["duree_tentative_s"] = round(
                        time.monotonic() - debut_tentative, 3
                    )
                    metriques["duree_totale_s"] = round(
                        time.monotonic() - debut, 3
                    )
        finally:
            metriques["duree_totale_s"] = round(time.monotonic() - debut, 3)

    def _completer(
        self,
        messages: list[dict[str, str]],
        temperature: float,
        response_format: dict[str, object] | None = None,
        reasoning_effort: str | None = None,
        delai: int = DELAI_MAXIMUM_ALBERT,
        max_completion_tokens: int | None = None,
        top_p: float | None = None,
        exiger_reponse_transcript: bool = False,
    ) -> str:
        debut = time.monotonic()
        diagnostic: dict[str, str | int | float | None] = {
            "modele": self._config.modele,
            "temperature": temperature,
            "top_p": top_p,
            "raisonnement": reasoning_effort,
            "budget_completion": max_completion_tokens,
            "statut_http": None,
            "finish_reason": None,
            "contenu_caracteres": 0,
            "raisonnement_caracteres": 0,
            "duree_secondes": None,
        }
        try:
            with httpx.Client(timeout=delai) as client:
                corps: dict[str, object] = {
                    "model": self._config.modele,
                    "messages": messages,
                    "temperature": temperature,
                }
                if response_format:
                    corps["response_format"] = response_format
                if reasoning_effort:
                    corps["reasoning_effort"] = reasoning_effort
                if max_completion_tokens is not None:
                    corps["max_completion_tokens"] = max_completion_tokens
                if top_p is not None:
                    corps["top_p"] = top_p
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
            diagnostic["statut_http"] = (
                erreur.response.status_code
                if isinstance(erreur, httpx.HTTPStatusError)
                and erreur.response is not None
                else None
            )
            traduit = _traduit_erreur(erreur)
            if exiger_reponse_transcript:
                diagnostic["duree_secondes"] = round(time.monotonic() - debut, 3)
                traduit.diagnostic = diagnostic
            raise traduit from erreur
        try:
            donnees = reponse.json()
            if exiger_reponse_transcript:
                diagnostic.update(_metriques_reponse_transcript(donnees))
            lecteur = (
                _lire_reponse_completion_transcript
                if exiger_reponse_transcript
                else _lire_reponse_completion
            )
            contenu = lecteur(donnees)
            if exiger_reponse_transcript:
                diagnostic["statut_http"] = reponse.status_code
                diagnostic["duree_secondes"] = round(time.monotonic() - debut, 3)
                return CompletionTranscript(contenu, diagnostic)
            return contenu
        except (
            ValueError,
            KeyError,
            IndexError,
            TypeError,
            ReponseAlbertInvalide,
        ) as erreur:
            invalide = ReponseAlbertInvalide()
            if exiger_reponse_transcript:
                diagnostic["statut_http"] = reponse.status_code
                diagnostic["duree_secondes"] = round(time.monotonic() - debut, 3)
                diagnostic["code_reponse"] = (
                    "json_reponse_invalide"
                    if isinstance(erreur, ValueError)
                    else "finish_reason_invalide"
                    if diagnostic.get("finish_reason") != "stop"
                    else "contenu_completion_invalide"
                )
                invalide.diagnostic = diagnostic
            raise invalide from erreur

    def completer_json_raisonnement_transcript(
        self,
        messages: list[dict[str, str]],
        nom_schema: str,
        schema: dict[str, object],
        effort: str,
        temperature: float = 0.0,
        top_p: float | None = None,
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
            effort,
            self._config.delai_transcripts,
            self._config.max_completion_tokens_transcripts,
            top_p,
            exiger_reponse_transcript=True,
        )

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
