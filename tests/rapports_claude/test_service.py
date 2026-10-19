from datetime import datetime, timezone
from uuid import uuid4

import pytest

from infra.memoire.depot_rapports_claude import DepotRapportsClaudeDeTest
from rapports_claude.depot import (
    ConflitIdempotence,
    EntreeInvalide,
    RapportIntrouvable,
    SourceIntrouvable,
    SourceModifiee,
    SourceNonEligible,
    SourceTranscriptClaude,
)
from rapports_claude.service import (
    TAILLE_BLOC,
    TAILLE_RAPPORT_MAXIMALE,
    ServiceRapportsClaude,
    empreinte_source,
)


def source(
    id: int = 1,
    type_source: str = "produit",
    revision: int = 1,
    confirme: bool = True,
    contenu: str = "transcript synthétique",
) -> SourceTranscriptClaude:
    return SourceTranscriptClaude(
        id,
        type_source,
        7,
        3 if type_source == "produit" else None,
        revision,
        confirme,
        contenu,
        "contexte synthétique",
        [{"id": "SPEAKER_01", "nom": "Participant 1"}],
        datetime.now(timezone.utc),
    )


def service_avec(
    source_initiale: SourceTranscriptClaude,
) -> tuple[ServiceRapportsClaude, DepotRapportsClaudeDeTest]:
    depot = DepotRapportsClaudeDeTest()
    depot.ajouter_source(source_initiale)
    return ServiceRapportsClaude(depot), depot


def test_catalogue_pagine_et_filtre_sur_analyses_courantes() -> None:
    service, depot = service_avec(source())
    depot.ajouter_source(source(2, "bizdev"))
    depot.ajouter_source(source(3, "ux"))
    premier = service.lister_transcripts(limite=1)
    assert [element.id for element in premier[0]] == [1]
    assert premier[1] == 1
    suivant = service.lister_transcripts(limite=1, curseur=premier[1])
    assert [element.id for element in suivant[0]] == [2]
    service.enregistrer_analyse(1, 1, empreinte_source(source()), uuid4(), "Analyse")
    analyses, _ = service.lister_transcripts(statut="analyses")
    non_analyses, _ = service.lister_transcripts(statut="non_analyses")
    assert [element.id for element in analyses] == [1]
    assert [element.id for element in non_analyses] == [2]


def test_source_se_lit_par_blocs_bornes_et_revision_verrouillee() -> None:
    service, depot = service_avec(source(contenu="é" * 30010))
    premier = service.lire_source(1)
    assert len(premier["bloc"]) == TAILLE_BLOC
    recompose = premier["bloc"]
    suivant = premier["offset_suivant"]
    while suivant is not None:
        bloc = service.lire_source(
            1, suivant, premier["revision"], premier["empreinte"]
        )
        recompose += bloc["bloc"]
        suivant = bloc["offset_suivant"]
    assert len(recompose) == premier["longueur_totale"]
    depot.ajouter_source(source(revision=2, contenu="nouveau contenu"))
    with pytest.raises(SourceModifiee):
        service.lire_source(1, TAILLE_BLOC, 1, premier["empreinte"])


def test_idempotence_rejoue_meme_rapport_et_refuse_une_autre_requete() -> None:
    service, depot = service_avec(source())
    empreinte = empreinte_source(source())
    cle = uuid4()
    premier = service.enregistrer_analyse(1, 1, empreinte, cle, "Analyse")
    depot.ajouter_source(source(revision=2, contenu="modifié"))
    rejoue = service.enregistrer_analyse(1, 1, empreinte, cle, "Analyse")
    assert rejoue.id == premier.id
    assert rejoue.courant is False
    with pytest.raises(ConflitIdempotence):
        service.enregistrer_analyse(1, 1, empreinte, cle, "Autre analyse")
    assert service.lire_rapport(premier.id)["courant"] is False
    assert service.lister_rapports(1)[0][0].courant is False


def test_ecriture_verifie_source_eligibilite_et_contenu() -> None:
    service, depot = service_avec(source())
    with pytest.raises(SourceIntrouvable):
        service.enregistrer_analyse(9, 1, "0" * 64, uuid4(), "Analyse")
    depot.ajouter_source(source(2, "ux"))
    with pytest.raises(SourceNonEligible):
        service.enregistrer_analyse(2, 1, "0" * 64, uuid4(), "Analyse")
    with pytest.raises(SourceModifiee):
        service.enregistrer_analyse(1, 2, "0" * 64, uuid4(), "Analyse")
    with pytest.raises(EntreeInvalide):
        service.enregistrer_analyse(1, 1, empreinte_source(source()), uuid4(), " \n")
    with pytest.raises(EntreeInvalide):
        service.enregistrer_analyse(
            1,
            1,
            empreinte_source(source()),
            uuid4(),
            "x" * (TAILLE_RAPPORT_MAXIMALE + 1),
        )


def test_lecture_rapport_inconnu_est_distincte() -> None:
    service, _ = service_avec(source())
    with pytest.raises(RapportIntrouvable):
        service.lire_rapport(10)
