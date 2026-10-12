import json
from datetime import date
from typing import cast

import pytest

from adaptateurs.exceptions import ErreurCommunicationAlbert
from infra.memoire.depot_transcripts_pdf import DepotTranscriptsPdfMemoire
from tests.adaptateurs.albert_de_test import AdaptateurAlbertDeTest
from transcripts_pdf.analyse import AnalysePdf, ServiceAnalysePdf
from transcripts_pdf.orchestration import (
    ServiceTranscriptsPdf,
    SourcePdfInvalide,
)
from transcripts_pdf.service import Locuteur


_NOM = "reunion-_zbq-okak-bsa_-du-2026-04-07-a-10_34.pdf"
_LOCUTEUR = [Locuteur("SPEAKER_01", "externe", "Participant externe.")]
_ANALYSE = {
    "resume": "Résumé.",
    "themes": [],
    "enjeux": [],
    "besoins_globaux": [],
    "freins": [],
    "motivations": [],
    "opportunites": [],
    "propositions": [],
    "signaux_positifs": [],
    "suites_evoquees": [],
    "fonctionnalites": [],
}


def _service(
    reponse_analyse: str = json.dumps(_ANALYSE), sans_appel_albert: bool = False
):
    albert = AdaptateurAlbertDeTest()
    if sans_appel_albert:
        albert.avec_erreur(AssertionError("Analyse non demandée."))
    else:
        albert.avec_reponse(reponse_analyse)
    return ServiceTranscriptsPdf(
        DepotTranscriptsPdfMemoire(),
        ServiceAnalysePdf(
            albert,
            {"produit": "prompt", "bizdev": "prompt"},
        ),
    )


def _confirmer(service: ServiceTranscriptsPdf, contenu: str = "SPEAKER_01: Besoin."):
    return service.confirmer(
        "bizdev", _NOM, 1, None, date(2026, 4, 7), contenu, "", _LOCUTEUR
    )


def test_confirme_analyse_et_retrouve_un_transcript_bizdev() -> None:
    service = _service(json.dumps(_ANALYSE))
    source = _confirmer(service)

    assert service.obtenir(source.id) == source
    assert service.lister(1) == [source]
    resultat = service.demarrer_analyse(source.id)
    assert resultat.analyse is None
    service.executer_job(resultat.job.id)
    assert service.obtenir_analyse(source.id).contenu["resume"] == "Résumé."
    assert service._depot.analyses[0].prompt_version == "bizdev-v6"
    assert service.demarrer_analyse(source.id).analyse is not None
    assert service.lister_jobs_a_reprendre() == []


def test_refuse_source_de_type_date_contenu_locuteur_ou_nom_invalide() -> None:
    service = _service()
    arguments = [
        "bizdev",
        _NOM,
        1,
        None,
        date(2026, 4, 7),
        "SPEAKER_01: Texte",
        "",
        _LOCUTEUR,
    ]
    for index, valeur in (
        (0, "invalid-type"),
        (1, "nom humain.pdf"),
        (2, 0),
        (3, 42),
        (4, None),
        (5, " "),
        (7, []),
    ):
        invalides = arguments.copy()
        invalides[index] = valeur
        with pytest.raises(SourcePdfInvalide):
            service.confirmer(*invalides)
    with pytest.raises(SourcePdfInvalide):
        service.confirmer(
            "bizdev",
            _NOM,
            1,
            None,
            date.today(),
            "SPEAKER_01: Texte",
            "",
            [Locuteur("SPEAKER_01", "inconnu", "")],
        )
    with pytest.raises(SourcePdfInvalide):
        service.confirmer(
            "produit",
            "transcript-bizdev-sans-date-deadbeef.pdf",
            1,
            1,
            date.today(),
            "SPEAKER_01: Texte",
            "",
            _LOCUTEUR,
        )
    source = service.confirmer(
        "bizdev",
        "transcript-BIZDEV-sans-date-deadbeef.pdf",
        1,
        None,
        date.today(),
        "SPEAKER_01: Texte",
        "",
        _LOCUTEUR,
    )
    assert source.nom_source == "transcript-BIZDEV-sans-date-deadbeef.pdf"
    with pytest.raises(SourcePdfInvalide):
        ServiceTranscriptsPdf._verifier(
            "invalid-type", 1, None, date.today(), "SPEAKER_01: Texte", _LOCUTEUR
        )


def test_exception_inattendue_de_l_analyse_echoue_le_job_sans_persistance(caplog) -> None:
    class AnalyseurEnEchecDeTest:
        def analyser(
            self,
            type_source: str,
            contenu: str,
            contexte: str,
            roles: list[dict[str, str]],
            schema_version: str,
        ) -> AnalysePdf:
            raise RuntimeError("IDENTITE_MASQUEE")

    depot = DepotTranscriptsPdfMemoire()
    service = ServiceTranscriptsPdf(
        depot,
        cast(ServiceAnalysePdf, AnalyseurEnEchecDeTest()),
    )
    source = _confirmer(service)
    job = service.demarrer_analyse(source.id).job

    service.executer_job(job.id)

    job_termine = depot.obtenir_job(source.id)
    assert job_termine is not None
    assert job_termine.statut == "echec"
    assert "phase=analyse code=exception_inattendue exception_type=RuntimeError" in caplog.text
    assert "IDENTITE_MASQUEE" not in caplog.text
    assert depot.analyses == []
    assert depot.fonctionnalites == []


def test_confirme_apres_validation_humaine_sans_appel_albert() -> None:
    service = _service(sans_appel_albert=True)

    source = _confirmer(service, "SPEAKER_01: Nom conservé après validation humaine.")

    assert service.obtenir(source.id) == source
    assert service.obtenir_analyse(source.id) is None
    assert service._depot.jobs == []


def test_modification_invalide_analyse_et_source_absente_reste_absente() -> None:
    service = _service()
    source = _confirmer(service)
    job = service.demarrer_analyse(source.id).job
    service.executer_job(job.id)

    modifie = service.modifier(
        source.id, date(2026, 4, 8), "SPEAKER_01: Nouveau.", "Contexte", _LOCUTEUR
    )
    assert modifie.revision == 2
    assert service.obtenir_analyse(source.id) is None
    assert service.modifier(99, date.today(), "Texte", "", []) is None
    with pytest.raises(SourcePdfInvalide):
        service.modifier(source.id, None, "Texte", "", [])
    assert service.supprimer(source.id)
    assert not service.supprimer(source.id)


def test_echoue_un_job_quand_la_revision_du_projet_a_change() -> None:
    service = _service()
    source = service._depot.ajouter(
        "produit",
        1,
        5,
        _NOM,
        date(2026, 4, 7),
        "SPEAKER_01: Texte",
        "",
        [_LOCUTEUR[0]._asdict()],
    )
    job = service._depot.creer_job(source.id)
    service._depot.sources[0] = source._replace(revision_projet=2)

    service.executer_job(job.id)

    assert service._depot.obtenir_job(source.id).statut == "echec"


def test_echec_analyse_est_visible_et_peut_etre_relancee(caplog) -> None:
    service = _service("réponse invalide")
    source = _confirmer(service)
    job = service.demarrer_analyse(source.id).job
    service.executer_job(job.id)
    assert service._depot.obtenir_job(source.id).statut == "echec"
    assert "phase=lecture_json code=json_invalide" in caplog.text
    depot = cast(DepotTranscriptsPdfMemoire, service._depot)
    assert depot.analyses == []
    assert depot.fonctionnalites == []
    relance = service.demarrer_analyse(source.id, relancer=True)
    assert relance.job.statut == "attente"
    service.executer_job(relance.job.id)
    job_termine = depot.obtenir_job(source.id)
    assert job_termine is not None
    assert job_termine.statut == "echec"
    service.executer_job(relance.job.id)


@pytest.mark.parametrize(
    ("reponse", "phase", "code"),
    [
        ("{}", "lecture_json", "cles_racine_invalides"),
        (
            json.dumps(
                {
                    **_ANALYSE,
                    "freins": [
                        {
                            "description": "Prix",
                            "reference": {"tour_id": 1, "token_debut": 0},
                        }
                    ],
                }
            ),
            "structure",
            "extraction_bizdev_invalide",
        ),
        (
            json.dumps(
                {
                    **_ANALYSE,
                    "freins": [
                        {
                            "description": "Prix",
                            "reference": {
                                "tour_id": 1,
                                "token_debut": 20,
                                "token_fin": 21,
                            },
                        }
                    ],
                }
            ),
            "references",
            "positions_hors_limites",
        ),
    ],
)
def test_echec_analyse_journalise_phase_sans_contenu(
    caplog, reponse: str, phase: str, code: str
) -> None:
    service = _service(reponse)
    source = _confirmer(service)
    job = service.demarrer_analyse(source.id).job

    service.executer_job(job.id)

    assert f"phase={phase} code={code}" in caplog.text
    if phase == "references":
        assert "token_debut=20" in caplog.text
    assert service._depot.obtenir_job(source.id).statut == "echec"
    assert service._depot.analyses == []
    assert service._depot.fonctionnalites == []


def test_echec_albert_journalise_sous_code_sans_message(caplog) -> None:
    albert = AdaptateurAlbertDeTest().avec_erreur(
        ErreurCommunicationAlbert("IDENTITE_MASQUEE")
    )
    service = ServiceTranscriptsPdf(
        DepotTranscriptsPdfMemoire(),
        ServiceAnalysePdf(albert, {"produit": "prompt", "bizdev": "prompt"}),
    )
    source = _confirmer(service)
    job = service.demarrer_analyse(source.id).job

    service.executer_job(job.id)

    assert "phase=appel_albert code=ErreurCommunicationAlbert" in caplog.text
    assert "IDENTITE_MASQUEE" not in caplog.text
    depot = cast(DepotTranscriptsPdfMemoire, service._depot)
    assert depot.analyses == []
    assert depot.fonctionnalites == []


def test_echec_finalisation_journalise_phase_et_ne_persiste_rien(caplog) -> None:
    class DepotEnEchecFinalisationDeTest(DepotTranscriptsPdfMemoire):
        def finaliser(self, *args, **kwargs):
            raise RuntimeError("IDENTITE_MASQUEE")

    depot = DepotEnEchecFinalisationDeTest()
    service = ServiceTranscriptsPdf(
        depot,
        ServiceAnalysePdf(
            AdaptateurAlbertDeTest().avec_reponse(json.dumps(_ANALYSE)),
            {"produit": "prompt", "bizdev": "prompt"},
        ),
    )
    source = _confirmer(service)
    job = service.demarrer_analyse(source.id).job

    service.executer_job(job.id)

    assert "phase=finalisation code=exception_persistance" in caplog.text
    assert "IDENTITE_MASQUEE" not in caplog.text
    assert depot.analyses == []
    assert depot.fonctionnalites == []
    job_termine = depot.obtenir_job(source.id)
    assert job_termine is not None
    assert job_termine.statut == "echec"


def test_finalisation_refusee_echoue_le_job(caplog) -> None:
    class DepotSansClaimDeTest(DepotTranscriptsPdfMemoire):
        def finaliser(self, *args, **kwargs):
            return False

    depot = DepotSansClaimDeTest()
    service = ServiceTranscriptsPdf(
        depot,
        ServiceAnalysePdf(
            AdaptateurAlbertDeTest().avec_reponse(json.dumps(_ANALYSE)),
            {"produit": "prompt", "bizdev": "prompt"},
        ),
    )
    source = _confirmer(service)
    job = service.demarrer_analyse(source.id).job

    service.executer_job(job.id)

    assert "phase=finalisation code=claim_ou_revision_invalide" in caplog.text
    job_termine = depot.obtenir_job(source.id)
    assert job_termine is not None
    assert job_termine.statut == "echec"


def test_demarrage_et_modification_refusent_les_identifiants_absents() -> None:
    service = _service()
    with pytest.raises(SourcePdfInvalide):
        service.demarrer_analyse(99)
    with pytest.raises(SourcePdfInvalide):
        service.confirmer(
            "bizdev", _NOM, 1, None, date.today(), "SPEAKER_02: Texte", "", _LOCUTEUR
        )
