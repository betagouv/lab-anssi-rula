import json
from datetime import date

import pytest

from infra.memoire.depot_transcripts_pdf import DepotTranscriptsPdfMemoire
from tests.adaptateurs.albert_de_test import AdaptateurAlbertDeTest
from transcripts_pdf.analyse import ServiceAnalysePdf
from transcripts_pdf.orchestration import (
    ServiceTranscriptsPdf,
    SourcePdfInvalide,
    SourcePdfNonAnonyme,
)
from transcripts_pdf.service import Locuteur
from validation_transcript.service import ServiceValidationTranscript


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


def _service(reponse_garde_fou: str, reponse_analyse: str | None = None):
    return ServiceTranscriptsPdf(
        DepotTranscriptsPdfMemoire(),
        ServiceValidationTranscript(
            AdaptateurAlbertDeTest().avec_reponse(reponse_garde_fou), "prompt"
        ),
        ServiceAnalysePdf(
            AdaptateurAlbertDeTest().avec_reponse(
                reponse_analyse or json.dumps(_ANALYSE)
            ),
            {"produit": "prompt", "bizdev": "prompt"},
        ),
    )


def _confirmer(service: ServiceTranscriptsPdf, contenu: str = "SPEAKER_01: Besoin."):
    return service.confirmer(
        "bizdev", _NOM, 1, None, date(2026, 4, 7), contenu, "", _LOCUTEUR
    )


def test_confirme_analyse_et_retrouve_un_transcript_bizdev() -> None:
    service = _service('{"valide": true, "problemes": []}')
    source = _confirmer(service)

    assert service.obtenir(source.id) == source
    assert service.lister(1) == [source]
    resultat = service.demarrer_analyse(source.id)
    assert resultat.analyse is None
    service.executer_job(resultat.job.id)
    assert service.obtenir_analyse(source.id).contenu["resume"] == "Résumé."
    assert service.demarrer_analyse(source.id).analyse is not None
    assert service.lister_jobs_a_reprendre() == []


def test_refuse_source_de_type_date_contenu_locuteur_ou_nom_invalide() -> None:
    service = _service('{"valide": true, "problemes": []}')
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
        (0, "autre"),
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


def test_refuse_un_transcript_si_le_garde_fou_signale_des_donnees() -> None:
    service = _service(
        '{"valide": false, "problemes": [{"categorie":"identite","element":"Nom test","raison":"Anonymiser."}]}'
    )

    with pytest.raises(SourcePdfNonAnonyme) as erreur:
        _confirmer(service)

    assert erreur.value.problemes[0]["raison"] == "Anonymiser."


def test_modification_invalide_analyse_et_source_absente_reste_absente() -> None:
    service = _service('{"valide": true, "problemes": []}')
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
    service = _service('{"valide": true, "problemes": []}')
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


def test_echec_analyse_est_visible_et_peut_etre_relancee() -> None:
    service = _service('{"valide": true, "problemes": []}', "réponse invalide")
    source = _confirmer(service)
    job = service.demarrer_analyse(source.id).job
    service.executer_job(job.id)
    assert service._depot.obtenir_job(source.id).statut == "echec"
    relance = service.demarrer_analyse(source.id, relancer=True)
    assert relance.job.statut == "attente"
    service.executer_job(relance.job.id)
    assert service._depot.obtenir_job(source.id).statut == "echec"
    service.executer_job(relance.job.id)


def test_demarrage_et_modification_refusent_les_identifiants_absents() -> None:
    service = _service('{"valide": true, "problemes": []}')
    with pytest.raises(SourcePdfInvalide):
        service.demarrer_analyse(99)
    with pytest.raises(SourcePdfInvalide):
        service.confirmer(
            "bizdev", _NOM, 1, None, date.today(), "SPEAKER_02: Texte", "", _LOCUTEUR
        )
