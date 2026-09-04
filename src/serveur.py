from pathlib import Path
from typing import cast

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from api.api import routeur
from api.erreurs import detail_erreur_validation
from adaptateurs.exceptions import ErreurAlbert
from configuration import charge_configuration

_config = charge_configuration()
REPERTOIRE_FRONTEND = Path(__file__).resolve().parents[1] / "ui" / "dist"

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[f"{_config.rula.max_requetes_par_minute}/minute"],
)

app = FastAPI(title="RULA", version="0.1.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]


def gestion_erreur_albert(_: Request, erreur: Exception) -> JSONResponse:
    erreur_albert = cast(ErreurAlbert, erreur)
    return JSONResponse(
        status_code=erreur_albert.statut_http,
        content={"detail": erreur_albert.detail},
    )


def gestion_erreur_validation(
    _: Request, erreur: Exception
) -> JSONResponse:
    erreur_validation = cast(RequestValidationError, erreur)
    return JSONResponse(
        status_code=422,
        content={"detail": detail_erreur_validation(erreur_validation.errors())},
    )


app.add_exception_handler(ErreurAlbert, gestion_erreur_albert)
app.add_exception_handler(RequestValidationError, gestion_erreur_validation)

app.include_router(routeur, prefix="/api")


def ajoute_frontend(
    app_fastapi: FastAPI, repertoire: Path = REPERTOIRE_FRONTEND
) -> bool:
    if not (repertoire / "index.html").is_file():
        return False
    app_fastapi.mount(
        "/", StaticFiles(directory=repertoire, html=True), name="frontend"
    )
    return True


ajoute_frontend(app)
