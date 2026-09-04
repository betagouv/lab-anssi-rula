from collections.abc import Sequence

_LIBELLES = {
    "participant": "le prénom de l’utilisateur",
    "date_entretien": "la date de l’entretien",
    "moderateur": "le modérateur",
    "contenu": "le transcript de l’entretien",
    "confirmation": "la confirmation de préparation",
    "projet_id": "le projet",
    "nouveau_projet": "le projet",
    "nom": "le nom du projet",
    "produit_id": "le produit",
    "entretien": "les informations de l’entretien",
    "identite_id": "l’identité",
    "nouvelle_identite": "la nouvelle identité",
    "nouveau_produit": "le nouveau projet",
}


def _nom_champ(erreur: dict[str, object]) -> str:
    emplacement = erreur.get("loc")
    if isinstance(emplacement, Sequence) and emplacement:
        champ = emplacement[-1]
        if isinstance(champ, str):
            return champ
    return "saisi"


def _message_champ(erreur: dict[str, object]) -> str:
    champ = _nom_champ(erreur)
    libelle = _LIBELLES.get(champ, f"le champ {champ}")
    if champ == "date_entretien" and erreur.get("type") != "missing":
        return "La date de l’entretien est invalide."
    if erreur.get("type") == "missing" or champ in _LIBELLES:
        return f"Le renseignement concernant {libelle} est obligatoire."
    return f"Le champ {champ} est invalide."


def detail_erreur_validation(
    erreurs: Sequence[dict[str, object]],
) -> dict[str, object]:
    messages = list(dict.fromkeys(_message_champ(erreur) for erreur in erreurs))
    return {
        "message": "Vérifiez les champs obligatoires avant de continuer.",
        "champs": messages,
    }
