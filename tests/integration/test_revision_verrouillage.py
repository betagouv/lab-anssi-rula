import os
import threading
import time
from uuid import uuid4

import psycopg2
import pytest

from configuration import charge_configuration
from infra.postgres.depot_analyse import DepotAnalysePostgres
from infra.postgres.depot_produits import DepotProduitsPostgres
from infra.postgres.depot_projets import DepotProjetsPostgres

pytestmark = pytest.mark.skipif(
    os.getenv("RULA_TEST_POSTGRES") != "1", reason="PostgreSQL integration disabled"
)


@pytest.mark.parametrize("cible", ["scan", "etape"])
def test_ecriture_obsolete_attend_le_verrou_et_est_rejetee(cible: str) -> None:
    config = charge_configuration().base_de_donnees
    identifiant = uuid4().hex
    produit = DepotProduitsPostgres(config).ajouter(f"integration-{identifiant}")
    projets = DepotProjetsPostgres(config)
    projet = projets.ajouter(produit.id, f"integration-{identifiant}", "")
    analyses = DepotAnalysePostgres(config)
    if cible == "etape":
        analyses.initialiser_etapes(projet.id)
    connexion = psycopg2.connect(
        host=config.hote,
        dbname=config.nom,
        user=config.utilisateur,
        password=config.mot_de_passe,
        port=config.port,
    )
    connexion.autocommit = False
    demarree = threading.Event()
    resultat: list[object] = []
    thread: threading.Thread | None = None

    def ecrire() -> None:
        demarree.set()
        try:
            resultat.append(
                projets.enregistrer_scan_si_revision(
                    projet.id, projet.revision_corpus, "stale"
                )
                if cible == "scan"
                else analyses.enregistrer_etape_si_revision(
                    projet.id, "scan-neutre", "prompt", "stale", projet.revision_corpus
                )
            )
        except Exception as erreur:
            resultat.append(erreur)

    try:
        with connexion.cursor() as curseur:
            curseur.execute(
                "UPDATE projets_recherche SET revision_corpus = revision_corpus + 1 WHERE id = %s",
                (projet.id,),
            )
        thread = threading.Thread(target=ecrire)
        thread.start()
        assert demarree.wait(2)
        time.sleep(0.2)
        assert thread.is_alive()
        connexion.commit()
        thread.join(5)
        assert not thread.is_alive()
        assert resultat == [None]
        if cible == "scan":
            assert projets.obtenir_scan(projet.id) is None
        else:
            etape = analyses.obtenir_etape(projet.id, "scan-neutre")
            assert etape is not None and etape.brouillon is None
    finally:
        connexion.rollback()
        if thread is not None:
            thread.join(5)
        connexion.close()
        projets.supprimer(projet.id)
