from abc import ABC, abstractmethod
import asyncio
import json
import time

import httpx

from configuration import Albert
from adaptateurs.exceptions import (
    DelaiAlbertDepasse,
    ErreurAlbert,
    ErreurCommunicationAlbert,
    ErreurHTTPAlbert,
    ReponseAlbertInvalide,
)


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


class AdaptateurAlbert(ABC):
    @abstractmethod
    def completer_json_raisonnement_preparation(
        self,
        messages: list[dict[str, str]],
        nom_schema: str,
        schema: dict[str, object],
        effort: str,
        temperature: float | None = None,
    ) -> str: ...


class AdaptateurAlbertReel(AdaptateurAlbert):
    def __init__(self, config: Albert) -> None:
        self._config = config

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
                        duree_tentative_s=round(time.monotonic() - debut_tentative, 3),
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
                    metriques["duree_totale_s"] = round(time.monotonic() - debut, 3)
        finally:
            metriques["duree_totale_s"] = round(time.monotonic() - debut, 3)
