from datetime import date, datetime, timedelta

import pytest

from infra.memoire.depot_transcripts_pdf import DepotTranscriptsPdfMemoire
from infra.postgres.depot_transcripts_pdf import DepotTranscriptsPdfPostgres
from transcripts_pdf.depot import (
    AnalyseTranscriptPdf,
    DepotTranscriptsPdf,
    JobAnalyseTranscript,
)


def ajoute_source(
    depot: DepotTranscriptsPdfMemoire,
    produit_id: int = 1,
    projet_id: int | None = None,
):
    return depot.ajouter(
        "produit",
        produit_id,
        projet_id,
        "entretien.pdf",
        date(2026, 4, 7),
        "verbatim",
        "contexte",
        [],
    )


def ajoute_job_reclame(
    depot: DepotTranscriptsPdfMemoire, projet_id: int | None = None
):
    source = ajoute_source(depot, projet_id=projet_id)
    job = depot.creer_job(source.id)
    reclame = depot.reclamer_job(job.id)
    assert reclame is not None
    return source, reclame


def test_ajoute_obtient_et_liste_les_sources() -> None:
    depot = DepotTranscriptsPdfMemoire()
    sans_projet = ajoute_source(depot)
    avec_projet = ajoute_source(depot, projet_id=42)
    autre_produit = ajoute_source(depot, produit_id=2)

    assert sans_projet.revision_projet is None
    assert avec_projet.revision_projet == 1
    assert depot.obtenir(sans_projet.id) == sans_projet
    assert depot.obtenir(999) is None
    assert depot.lister(1) == [sans_projet, avec_projet]
    assert depot.lister(2) == [autre_produit]


def test_modifier_invalide_les_donnees_associees() -> None:
    depot = DepotTranscriptsPdfMemoire()
    source = ajoute_source(depot, projet_id=42)
    autre = ajoute_source(depot, projet_id=43)
    depot.creer_job(source.id)
    depot.creer_job(autre.id)
    depot.analyses = [
        AnalyseTranscriptPdf(1, source.id, 1, "produit", {}, "1", "1", datetime.now()),
        AnalyseTranscriptPdf(2, autre.id, 1, "produit", {}, "1", "1", datetime.now()),
    ]
    depot.fonctionnalites = [
        {"transcript_id": source.id},
        {"transcript_id": autre.id},
    ]

    assert depot.modifier(999, date(2026, 4, 8), "", "", []) is None
    modifiee = depot.modifier(source.id, date(2026, 4, 8), "nouveau", "contexte", [])

    assert modifiee is not None
    assert (modifiee.revision, modifiee.revision_projet) == (2, 2)
    assert depot.analyses == [depot.analyses[0]]
    assert depot.analyses[0].transcript_id == autre.id
    assert depot.fonctionnalites == [{"transcript_id": autre.id}]
    assert [job.transcript_id for job in depot.jobs] == [autre.id]

    sans_projet = ajoute_source(depot)
    modifiee_sans_projet = depot.modifier(
        sans_projet.id, date(2026, 4, 9), "nouveau", "contexte", []
    )
    assert modifiee_sans_projet is not None
    assert modifiee_sans_projet.revision_projet is None


def test_supprime_une_source_et_ses_analyses_jobs() -> None:
    depot = DepotTranscriptsPdfMemoire()
    source = ajoute_source(depot)
    depot.creer_job(source.id)
    depot.analyses = [
        AnalyseTranscriptPdf(1, source.id, 1, "produit", {}, "1", "1", datetime.now())
    ]

    assert not depot.supprimer(999)
    assert depot.supprimer(source.id)
    assert depot.obtenir(source.id) is None
    assert depot.obtenir_analyse(source.id) is None
    assert depot.jobs == []


def test_cree_reclame_enregistre_et_relance_un_job() -> None:
    depot = DepotTranscriptsPdfMemoire()
    with pytest.raises(ValueError, match="Transcript confirmé introuvable"):
        depot.creer_job(999)

    source = ajoute_source(depot)
    assert depot.obtenir_job(source.id) is None
    job = depot.creer_job(source.id)
    assert depot.creer_job(source.id) == job
    assert depot.obtenir_job(source.id) == job
    assert depot.lister_jobs_a_reprendre() == [job.id]
    assert depot.reclamer_job(999) is None

    reclame = depot.reclamer_job(job.id)
    assert reclame is not None
    assert depot.reclamer_job(job.id) is None
    depot.jobs[0] = reclame._replace(bail_jusqua=None)
    assert depot.reclamer_job(job.id) is None
    depot.jobs[0] = reclame._replace(bail_jusqua=datetime.now() - timedelta(seconds=1))
    assert depot.lister_jobs_a_reprendre() == [job.id]
    relance = depot.reclamer_job(job.id)
    assert relance is not None
    assert relance.jeton != reclame.jeton

    depot.echouer(999, "inconnu", "erreur")
    depot.echouer(job.id, "mauvais jeton", "erreur")
    assert depot.obtenir_job(source.id) == relance
    depot.echouer(job.id, relance.jeton or "", "erreur")
    job_en_echec = depot.obtenir_job(source.id)
    assert job_en_echec is not None and job_en_echec.statut == "echec"
    assert depot.creer_job(source.id, relancer=True).statut == "attente"
    assert depot.creer_job(source.id, relancer=True).statut == "attente"


def test_finaliser_refuse_les_jobs_obsoletes() -> None:
    depot = DepotTranscriptsPdfMemoire()
    source = ajoute_source(depot)
    job = depot.creer_job(source.id)

    sans_job_courant = JobAnalyseTranscript(
        999, source.id, source.revision, source.revision_projet, "en_cours", "jeton", None
    )
    assert not depot.finaliser(sans_job_courant, {}, [], "1", "1")

    depot.sources.clear()
    assert not depot.finaliser(job, {}, [], "1", "1")

    source, job_reclame = ajoute_job_reclame(depot)
    assert not depot.finaliser(
        job_reclame._replace(jeton="mauvais"), {}, [], "1", "1"
    )

    depot.sources[0] = source._replace(revision=source.revision + 1)
    assert not depot.finaliser(job_reclame, {}, [], "1", "1")

    source, job_reclame = ajoute_job_reclame(depot, projet_id=42)
    depot.sources[0] = source._replace(revision_projet=2)
    assert not depot.finaliser(job_reclame, {}, [], "1", "1")


def test_finalise_une_analyse_et_ses_fonctionnalites() -> None:
    depot = DepotTranscriptsPdfMemoire()
    source, job = ajoute_job_reclame(depot, projet_id=42)

    assert depot.finaliser(job, {"resume": "résumé"}, [{"nom": "export"}], "1", "2")
    analyse = depot.obtenir_analyse(source.id)

    assert analyse is not None
    assert analyse.contenu == {"resume": "résumé"}
    assert analyse.type_source == "produit"
    assert depot.fonctionnalites == [{"transcript_id": source.id, "nom": "export"}]
    job_termine = depot.obtenir_job(source.id)
    assert job_termine is not None and job_termine.statut == "termine"


def test_depot_postgres_implemente_le_contrat() -> None:
    assert issubclass(DepotTranscriptsPdfPostgres, DepotTranscriptsPdf)