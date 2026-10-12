import asyncio
from pathlib import Path

from fastapi import FastAPI

from serveur import (
    ajoute_frontend,
    arrete_surveillance_jobs,
    demarre_surveillance_jobs,
)


def test_surveillance_jobs_demarre_et_sarrete_proprement() -> None:
    app = FastAPI()
    scans = 0

    def scanner() -> None:
        nonlocal scans
        scans += 1

    async def executer() -> None:
        await demarre_surveillance_jobs(app, scanner)
        while scans == 0:
            await asyncio.sleep(0)
        await arrete_surveillance_jobs(app)

    asyncio.run(executer())

    assert scans == 1


def test_ajoute_frontend_si_le_bundle_existe(tmp_path: Path) -> None:
    app = FastAPI()
    (tmp_path / "index.html").write_text("<main>RULA</main>")

    assert ajoute_frontend(app, tmp_path)


def test_ajoute_frontend_si_le_bundle_est_absent(tmp_path: Path) -> None:
    app = FastAPI()

    assert not ajoute_frontend(app, tmp_path)
