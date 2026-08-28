from collections.abc import Callable
from typing import Any

from fastapi import HTTPException

from projets.depot import DepotProjets, Projet
from projets.service import ProjetDejaExistant
from produits.depot import DepotProduits
from validation_transcript.service import ServiceValidationTranscript


def verifier_import(
    contenu: str, confirmation: bool, validation: ServiceValidationTranscript
) -> None:
    if not confirmation:
        raise HTTPException(status_code=422, detail="Confirmation obligatoire")
    if not validation.valider(contenu).valide:
        raise HTTPException(status_code=422, detail="Contenu non conforme")


def selectionner_projet(
    produit_id: int,
    projet_id: int | None,
    nouveau_nom: str | None,
    nouveau_brief: str,
    projets: DepotProjets,
    produits: DepotProduits,
) -> tuple[Projet, bool]:
    if not any(produit.id == produit_id for produit in produits.lister()):
        raise HTTPException(status_code=404, detail="Produit introuvable.")
    if (projet_id is None) == (nouveau_nom is None):
        raise HTTPException(
            status_code=422,
            detail="Sélectionnez un projet existant ou créez un nouveau projet.",
        )
    if projet_id is not None:
        projet = projets.obtenir(projet_id)
        if not projet or projet.produit_id != produit_id:
            raise HTTPException(
                status_code=404, detail="Projet introuvable pour ce produit."
            )
        return projet, False
    assert nouveau_nom is not None
    nom = nouveau_nom.strip()
    if not nom:
        raise HTTPException(status_code=422, detail="Le nom du projet est obligatoire.")
    if any(
        projet.produit_id == produit_id and projet.nom.strip().lower() == nom.lower()
        for projet in projets.lister(produit_id)
    ):
        raise HTTPException(
            status_code=409, detail="Ce projet existe déjà pour ce produit."
        )
    try:
        return projets.ajouter(produit_id, nom, nouveau_brief), True
    except ProjetDejaExistant as erreur:
        raise HTTPException(
            status_code=409, detail="Ce projet existe déjà pour ce produit."
        ) from erreur


def importer_source_csv(
    produit_id: int,
    contenu: str,
    confirmation: bool,
    projet_id: int | None,
    nouveau_nom: str | None,
    nouveau_brief: str,
    validation: ServiceValidationTranscript,
    projets: DepotProjets,
    produits: DepotProduits,
    importer: Callable[[int, str, int], list[Any]],
) -> dict[str, Any]:
    verifier_import(contenu, confirmation, validation)
    projet, cree = selectionner_projet(
        produit_id,
        projet_id,
        nouveau_nom,
        nouveau_brief,
        projets,
        produits,
    )
    try:
        sources = importer(produit_id, contenu, projet.id)
    except (KeyError, ValueError) as erreur:
        if cree:
            projets.supprimer(projet.id)
        raise HTTPException(
            status_code=400, detail=f"CSV invalide : {erreur}"
        ) from erreur
    except Exception:
        if cree:
            projets.supprimer(projet.id)
        raise
    return {
        "projet": projet._asdict(),
        "sources": [source._asdict() for source in sources],
    }
