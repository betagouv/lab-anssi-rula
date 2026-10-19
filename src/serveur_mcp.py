from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from datetime import datetime
from hmac import compare_digest
from typing import Any, Literal
from uuid import UUID

import psycopg2
from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from starlette.applications import Starlette
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route

from configuration import Configuration, charge_configuration
from infra.postgres.depot_rapports_claude import DepotRapportsClaudePostgres
from rapports_claude.depot import (
    ConflitIdempotence,
    EntreeInvalide,
    RapportIntrouvable,
    SourceIntrouvable,
    SourceModifiee,
    SourceNonEligible,
)
from rapports_claude.service import ServiceRapportsClaude


def fabrique_service_rapports_claude() -> ServiceRapportsClaude:
    return ServiceRapportsClaude(
        DepotRapportsClaudePostgres(charge_configuration().base_de_donnees)
    )


def verifie_schema(configuration: Configuration) -> None:
    base = configuration.base_de_donnees
    with psycopg2.connect(
        host=base.hote,
        port=base.port,
        dbname=base.nom,
        user=base.utilisateur,
        password=base.mot_de_passe,
    ) as connexion:
        with connexion.cursor() as curseur:
            curseur.execute(
                "SELECT id, type_source, produit_id, projet_id, revision_corpus, confirme, contenu, contexte, locuteurs, cree_le FROM transcripts LIMIT 0"
            )
            curseur.execute(
                "SELECT id, transcript_id, revision, empreinte, cle_idempotence, contenu_markdown, cree_le FROM rapports_claude LIMIT 0"
            )


def _avec_erreurs(outil: Callable[[], Any]) -> Any:
    try:
        return outil()
    except SourceIntrouvable as erreur:
        raise ToolError("Transcript introuvable") from erreur
    except RapportIntrouvable as erreur:
        raise ToolError("Rapport introuvable") from erreur
    except SourceNonEligible as erreur:
        raise ToolError("Transcript non éligible") from erreur
    except SourceModifiee as erreur:
        raise ToolError("Transcript modifié; relire la source") from erreur
    except ConflitIdempotence as erreur:
        raise ToolError(
            "Clé d’idempotence déjà utilisée pour une autre analyse"
        ) from erreur
    except EntreeInvalide as erreur:
        raise ToolError("Paramètres invalides") from erreur


def _date(valeur: datetime) -> str:
    return valeur.isoformat()


def _catalogue(element: Any) -> dict[str, object]:
    return {
        "id": element.id,
        "type_source": element.type_source,
        "produit_id": element.produit_id,
        "projet_id": element.projet_id,
        "revision": element.revision,
        "nombre_rapports": element.nombre_rapports,
        "analyse_courante": element.analyse_courante,
        "cree_le": _date(element.cree_le),
    }


def _rapport(element: Any) -> dict[str, object]:
    return {
        "id": element.id,
        "transcript_id": element.transcript_id,
        "revision": element.revision,
        "cree_le": _date(element.cree_le),
        "courant": element.courant,
    }


def fabrique_serveur_mcp(
    fabrique_service: Callable[
        [], ServiceRapportsClaude
    ] = fabrique_service_rapports_claude,
) -> MCPServer:
    serveur = MCPServer(
        "RULA rapports Claude",
        instructions="Les sources disponibles sont uniquement les transcripts confirmés produit et BizDev. Lire les blocs suivants avec la révision et l’empreinte du premier bloc.",
    )

    @serveur.tool(
        name="lister_transcripts",
        description="Liste les transcripts confirmés produit et BizDev sans exposer leur contenu ni leur nom.",
    )
    def lister_transcripts(
        produit_id: int | None = None,
        projet_id: int | None = None,
        type_source: Literal["produit", "bizdev"] | None = None,
        statut: Literal["tous", "analyses", "non_analyses"] = "tous",
        limite: int = 20,
        curseur: int | None = None,
    ) -> dict[str, object]:
        def executer() -> dict[str, object]:
            elements, suivant = fabrique_service().lister_transcripts(
                produit_id, projet_id, type_source, statut, limite, curseur
            )
            return {
                "elements": [_catalogue(element) for element in elements],
                "curseur_suivant": suivant,
            }

        return _avec_erreurs(executer)

    @serveur.tool(
        name="lire_transcript",
        description="Lit par blocs la source, son historique de rapports ou un rapport précis.",
    )
    def lire_transcript(
        mode: Literal["source", "historique", "rapport"],
        transcript_id: int | None = None,
        rapport_id: int | None = None,
        offset: int = 0,
        revision: int | None = None,
        empreinte: str | None = None,
        limite: int = 20,
        curseur: int | None = None,
    ) -> dict[str, object]:
        def executer() -> dict[str, object]:
            service = fabrique_service()
            if mode == "source" and transcript_id is not None:
                return service.lire_source(transcript_id, offset, revision, empreinte)
            if mode == "historique" and transcript_id is not None:
                elements, suivant = service.lister_rapports(
                    transcript_id, limite, curseur
                )
                return {
                    "elements": [_rapport(element) for element in elements],
                    "curseur_suivant": suivant,
                }
            if mode == "rapport" and rapport_id is not None:
                return service.lire_rapport(rapport_id, offset)
            raise EntreeInvalide

        return _avec_erreurs(executer)

    @serveur.tool(
        name="enregistrer_analyse",
        description="Enregistre un rapport Markdown idempotent pour la révision lue d’un transcript confirmé.",
    )
    def enregistrer_analyse(
        transcript_id: int,
        revision: int,
        empreinte: str,
        cle_idempotence: UUID,
        contenu: str,
    ) -> dict[str, object]:
        def executer() -> dict[str, object]:
            rapport = fabrique_service().enregistrer_analyse(
                transcript_id, revision, empreinte, cle_idempotence, contenu
            )
            return {
                "rapport_id": rapport.id,
                "transcript_id": rapport.transcript_id,
                "revision": rapport.revision,
                "cree_le": _date(rapport.cree_le),
                "courant": rapport.courant,
            }

        return _avec_erreurs(executer)

    return serveur


class MiddlewareBearer(BaseHTTPMiddleware):
    def __init__(self, app: Any, jeton: str) -> None:
        super().__init__(app)
        self._jeton = jeton

    async def dispatch(self, request: Request, call_next: Callable[..., Any]) -> Any:
        entete = request.headers.get("authorization", "")
        try:
            autorise = compare_digest(
                entete.encode("ascii"), f"Bearer {self._jeton}".encode("ascii")
            )
        except UnicodeEncodeError:
            autorise = False
        if request.url.path != "/healthz" and (not self._jeton or not autorise):
            return JSONResponse(
                {"detail": "Non autorisé"},
                status_code=401,
                headers={"WWW-Authenticate": "Bearer"},
            )
        return await call_next(request)


def cree_application_http(
    serveur: MCPServer,
    configuration: Configuration,
    verification_schema: Callable[[], None] | None = None,
) -> Starlette:
    jeton = configuration.mcp.jeton.get_secret_value()
    mcp_app = serveur.streamable_http_app(
        streamable_http_path="/mcp",
        json_response=True,
        stateless_http=True,
        host=configuration.mcp.hote,
    )

    @asynccontextmanager
    async def lifespan(_: Starlette) -> AsyncIterator[None]:
        if not jeton:
            raise RuntimeError(
                "RULA_MCP_BEARER_TOKEN est obligatoire pour le transport HTTP"
            )
        (verification_schema or (lambda: verifie_schema(configuration)))()
        async with serveur.session_manager.run():
            yield

    async def sante(_: Request) -> JSONResponse:
        return JSONResponse({"statut": "ok"})

    application = Starlette(
        routes=[Route("/healthz", sante), Mount("/", app=mcp_app)],
        lifespan=lifespan,
    )
    application.add_middleware(MiddlewareBearer, jeton=jeton)
    return application


configuration = charge_configuration()
serveur = fabrique_serveur_mcp()
app = cree_application_http(serveur, configuration)

if __name__ == "__main__":
    verifie_schema(configuration)
    serveur.run(transport="stdio")
