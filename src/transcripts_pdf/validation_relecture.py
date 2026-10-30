from typing import Any

from transcripts_pdf.protection_liste_blanche import (
    positions_liste_blanche,
    positions_liste_blanche_sans_locuteurs,
)


def verifier_etat_relecture(
    contenu_original: str,
    contexte_original: str,
    occurrences_imposees: list[dict[str, Any]],
    termes_imposes: tuple[str, ...],
    etat: dict[str, Any],
) -> tuple[str, str]:
    champs = {"transcript": contenu_original, "contexte": contexte_original}
    tables = {champ: _table_offsets(texte) for champ, texte in champs.items()}
    obligatoires = {
        "transcript": [
            (occurrence["debut"], occurrence["fin"])
            for occurrence in occurrences_imposees
            if occurrence["champ"] == "transcript"
        ]
        + positions_liste_blanche_sans_locuteurs(
            contenu_original, list(termes_imposes)
        ),
        "contexte": [
            (occurrence["debut"], occurrence["fin"])
            for occurrence in occurrences_imposees
            if occurrence["champ"] == "contexte"
        ]
        + positions_liste_blanche(contexte_original, list(termes_imposes)),
    }
    snapshots = [etat, *etat.get("annulations", []), *etat.get("retablissements", [])]
    projection = (contenu_original, contexte_original)
    for index, instantane in enumerate(snapshots):
        resultat = _verifier_instantane(
            champs, tables, obligatoires, termes_imposes, instantane
        )
        if index == 0:
            projection = resultat
    return projection


def verifier_projection_finale(
    contenu: str, contexte: str, termes_imposes: tuple[str, ...]
) -> None:
    if positions_liste_blanche_sans_locuteurs(
        contenu, list(termes_imposes)
    ) or positions_liste_blanche(contexte, list(termes_imposes)):
        raise ValueError("La projection contient une valeur à masquer.")


def _verifier_instantane(
    champs: dict[str, str],
    tables: dict[str, dict[int, int]],
    obligatoires: dict[str, list[tuple[int, int]]],
    termes_imposes: tuple[str, ...],
    instantane: dict[str, Any],
) -> tuple[str, str]:
    masques = instantane.get("masques", [])
    plages = instantane.get("plages", [])
    masques_par_id = {masque["identifiant"]: masque for masque in masques}
    if len(masques_par_id) != len(masques):
        raise ValueError("État de relecture incompatible.")
    if instantane.get("selection") not in {None, *masques_par_id}:
        raise ValueError("État de relecture incompatible.")
    intervalles: dict[str, list[tuple[int, int, str, bool]]] = {
        champ: [] for champ in champs
    }
    plage_ids: set[str] = set()
    valeur_par_masque: dict[str, str] = {}
    for plage in plages:
        if plage["identifiant"] in plage_ids:
            raise ValueError("État de relecture incompatible.")
        plage_ids.add(plage["identifiant"])
        masque = masques_par_id.get(plage["masque_identifiant"])
        source = champs.get(plage["champ"])
        if masque is None or source is None:
            raise ValueError("État de relecture incompatible.")
        debut, fin = _convertir_plage(
            tables[plage["champ"]], plage["debut"], plage["fin"]
        )
        valeur = source[debut:fin]
        if valeur_par_masque.setdefault(masque["identifiant"], valeur) != valeur:
            raise ValueError("État de relecture incompatible.")
        intervalles[plage["champ"]].append(
            (debut, fin, masque["identifiant"], masque["actif"])
        )
    for positions in intervalles.values():
        positions.sort()
        if any(
            position[0] < precedent[1]
            for precedent, position in zip(positions, positions[1:])
        ):
            raise ValueError("État de relecture incompatible.")
    actifs = {
        champ: [(debut, fin) for debut, fin, _, actif in positions if actif]
        for champ, positions in intervalles.items()
    }
    for champ, valeurs in obligatoires.items():
        for debut, fin in valeurs:
            curseur = debut
            for debut_actif, fin_actif in actifs[champ]:
                if debut_actif <= curseur < fin_actif:
                    curseur = max(curseur, fin_actif)
                    if curseur >= fin:
                        break
            if curseur < fin:
                raise ValueError("État de relecture incompatible.")
    projection: dict[str, str] = {}
    for champ, source in champs.items():
        resultat = source
        for debut, fin, identifiant, actif in reversed(intervalles[champ]):
            if actif:
                resultat = (
                    resultat[:debut]
                    + masques_par_id[identifiant]["valeur_anonyme"]
                    + resultat[fin:]
                )
        projection[champ] = resultat
    verifier_projection_finale(
        projection["transcript"], projection["contexte"], termes_imposes
    )
    return projection["transcript"], projection["contexte"]


def _table_offsets(texte: str) -> dict[int, int]:
    positions = {0: 0}
    unite = 0
    for index, caractere in enumerate(texte, 1):
        unite += 2 if ord(caractere) > 0xFFFF else 1
        positions[unite] = index
    return positions


def _convertir_plage(
    positions: dict[int, int], debut_utf16: int, fin_utf16: int
) -> tuple[int, int]:
    if (
        debut_utf16 not in positions
        or fin_utf16 not in positions
        or fin_utf16 <= debut_utf16
    ):
        raise ValueError("État de relecture incompatible.")
    return positions[debut_utf16], positions[fin_utf16]
