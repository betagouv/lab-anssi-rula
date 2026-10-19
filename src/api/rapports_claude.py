from fastapi import APIRouter, Depends, HTTPException, Query

from configuration import charge_configuration
from infra.postgres.depot_rapports_claude import DepotRapportsClaudePostgres
from rapports_claude.depot import (
    DepotRapportsClaude,
    EntreeInvalide,
    RapportIntrouvable,
    SourceIntrouvable,
    SourceModifiee,
    SourceNonEligible,
)
from rapports_claude.service import ServiceRapportsClaude

routeur = APIRouter()


def fabrique_service_rapports_claude() -> ServiceRapportsClaude:
    depot: DepotRapportsClaude = DepotRapportsClaudePostgres(
        charge_configuration().base_de_donnees
    )
    return ServiceRapportsClaude(depot)


@routeur.get("/rapports-claude/transcripts")
def lister_transcripts(
    produit_id: int | None = None,
    projet_id: int | None = None,
    type_source: str | None = None,
    statut: str = "tous",
    limite: int = Query(default=20, ge=1, le=100),
    curseur: int | None = Query(default=None, ge=0),
    service: ServiceRapportsClaude = Depends(fabrique_service_rapports_claude),
) -> dict[str, object]:
    try:
        elements, suivant = service.lister_transcripts(
            produit_id, projet_id, type_source, statut, limite, curseur
        )
    except EntreeInvalide as erreur:
        raise HTTPException(status_code=422, detail="Filtres invalides") from erreur
    return {
        "elements": [element._asdict() for element in elements],
        "curseur_suivant": suivant,
    }


@routeur.get("/rapports-claude/transcripts/{transcript_id}")
def lire_source(
    transcript_id: int,
    offset: int = Query(default=0, ge=0),
    revision: int | None = Query(default=None, ge=1),
    empreinte: str | None = Query(default=None, pattern="^[0-9a-f]{64}$"),
    service: ServiceRapportsClaude = Depends(fabrique_service_rapports_claude),
) -> dict[str, object]:
    try:
        return service.lire_source(transcript_id, offset, revision, empreinte)
    except SourceIntrouvable as erreur:
        raise HTTPException(
            status_code=404, detail="Transcript introuvable"
        ) from erreur
    except SourceNonEligible as erreur:
        raise HTTPException(
            status_code=422, detail="Transcript non éligible"
        ) from erreur
    except SourceModifiee as erreur:
        raise HTTPException(status_code=409, detail="Transcript modifié") from erreur
    except EntreeInvalide as erreur:
        raise HTTPException(status_code=422, detail="Lecture invalide") from erreur


@routeur.get("/rapports-claude/transcripts/{transcript_id}/rapports")
def lister_rapports(
    transcript_id: int,
    limite: int = Query(default=20, ge=1, le=100),
    curseur: int | None = Query(default=None, ge=0),
    service: ServiceRapportsClaude = Depends(fabrique_service_rapports_claude),
) -> dict[str, object]:
    try:
        rapports, suivant = service.lister_rapports(transcript_id, limite, curseur)
    except SourceIntrouvable as erreur:
        raise HTTPException(
            status_code=404, detail="Transcript introuvable"
        ) from erreur
    except SourceNonEligible as erreur:
        raise HTTPException(
            status_code=422, detail="Transcript non éligible"
        ) from erreur
    except EntreeInvalide as erreur:
        raise HTTPException(status_code=422, detail="Pagination invalide") from erreur
    return {
        "elements": [rapport._asdict() for rapport in rapports],
        "curseur_suivant": suivant,
    }


@routeur.get("/rapports-claude/{rapport_id}")
def lire_rapport(
    rapport_id: int,
    offset: int = Query(default=0, ge=0),
    service: ServiceRapportsClaude = Depends(fabrique_service_rapports_claude),
) -> dict[str, object]:
    try:
        return service.lire_rapport(rapport_id, offset)
    except RapportIntrouvable as erreur:
        raise HTTPException(status_code=404, detail="Rapport introuvable") from erreur
    except SourceNonEligible as erreur:
        raise HTTPException(
            status_code=422, detail="Transcript non éligible"
        ) from erreur
    except EntreeInvalide as erreur:
        raise HTTPException(status_code=422, detail="Lecture invalide") from erreur
