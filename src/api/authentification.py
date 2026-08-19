import base64
import binascii
import hmac

from fastapi import Request
from fastapi.responses import PlainTextResponse, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp


class AuthentificationBasicMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: ASGIApp,
        utilisateur: str,
        mot_de_passe: str,
        chemin_public: str = "/api/sante",
    ) -> None:
        super().__init__(app)
        self.utilisateur = utilisateur
        self.mot_de_passe = mot_de_passe
        self.chemin_public = chemin_public

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        if request.url.path == self.chemin_public or self._autorisation_valide(request):
            return await call_next(request)
        return PlainTextResponse(
            "Authentification requise",
            status_code=401,
            headers={"WWW-Authenticate": 'Basic realm="RULA"'},
        )

    def _autorisation_valide(self, request: Request) -> bool:
        autorisation = request.headers.get("Authorization", "")
        schema, separateur, valeur = autorisation.partition(" ")
        if not separateur or schema.lower() != "basic":
            return False

        try:
            identifiants = base64.b64decode(valeur, validate=True).decode("utf-8")
        except (binascii.Error, UnicodeDecodeError):
            return False

        utilisateur, separateur, mot_de_passe = identifiants.partition(":")
        return (
            bool(separateur)
            and hmac.compare_digest(utilisateur, self.utilisateur)
            and hmac.compare_digest(mot_de_passe, self.mot_de_passe)
        )
