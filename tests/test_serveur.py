from pathlib import Path

from fastapi import FastAPI

from serveur import ajoute_frontend


def test_ajoute_frontend_si_le_bundle_existe(tmp_path: Path) -> None:
    application = FastAPI()
    (tmp_path / "index.html").write_text("<main>RULA</main>")
    assert ajoute_frontend(application, tmp_path)


def test_ajoute_frontend_si_le_bundle_est_absent(tmp_path: Path) -> None:
    assert not ajoute_frontend(FastAPI(), tmp_path)
