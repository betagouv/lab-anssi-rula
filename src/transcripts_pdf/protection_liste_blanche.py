import unicodedata


def normaliser_pour_comparaison(texte: str) -> str:
    return "".join(_unites_normalisees(texte)[0])


def positions_liste_blanche(texte: str, termes: list[str]) -> list[tuple[int, int]]:
    normalise, positions, debuts_unites, fins_unites = _unites_normalisees(texte)
    protegees = []
    for terme in termes:
        recherche = normaliser_pour_comparaison(terme)
        depart = normalise.find(recherche)
        while recherche and depart >= 0:
            fin_normalisee = depart + len(recherche)
            debut = positions[depart][0]
            fin = positions[fin_normalisee - 1][1]
            if (
                debuts_unites[depart]
                and fins_unites[fin_normalisee - 1]
                and _frontiere(texte, debut, fin)
            ):
                protegees.append((debut, fin))
            depart = normalise.find(recherche, depart + 1)
    return _fusionner(protegees)


def soustraire_intervalle(
    texte: str, debut: int, fin: int, protegees: list[tuple[int, int]]
) -> list[tuple[int, int]]:
    if not any(
        debut_protege < fin and fin_protege > debut
        for debut_protege, fin_protege in protegees
    ):
        return [(debut, fin)] if any(c.isalnum() for c in texte[debut:fin]) else []
    morceaux = []
    curseur = debut
    for debut_protege, fin_protege in protegees:
        if fin_protege <= curseur or debut_protege >= fin:
            continue
        morceaux.extend(_morceau_utile(texte, curseur, min(debut_protege, fin)))
        curseur = max(curseur, fin_protege)
        if curseur >= fin:
            return morceaux
    morceaux.extend(_morceau_utile(texte, curseur, fin))
    return morceaux


def _unites_normalisees(
    texte: str,
) -> tuple[str, list[tuple[int, int]], list[bool], list[bool]]:
    normalise: list[str] = []
    positions: list[tuple[int, int]] = []
    debuts_unites: list[bool] = []
    fins_unites: list[bool] = []
    debut = 0
    while debut < len(texte):
        if texte[debut].isspace():
            fin = debut + 1
            while fin < len(texte) and texte[fin].isspace():
                fin += 1
            unite = " "
        else:
            fin = debut + 1
            if (
                _jamo_initial(texte[debut])
                and fin < len(texte)
                and _jamo_medial(texte[fin])
            ):
                fin += 1
                if fin < len(texte) and _jamo_final(texte[fin]):
                    fin += 1
            elif (
                _syllabe_hangul_sans_final(texte[debut])
                and fin < len(texte)
                and _jamo_final(texte[fin])
            ):
                fin += 1
            while fin < len(texte) and unicodedata.category(texte[fin]).startswith("M"):
                fin += 1
            unite = unicodedata.normalize("NFC", texte[debut:fin]).casefold()
            unite = unite.replace("’", "'")
        normalise.extend(unite)
        positions.extend([(debut, fin)] * len(unite))
        if unite:
            debuts_unites.extend([True] + [False] * (len(unite) - 1))
            fins_unites.extend([False] * (len(unite) - 1) + [True])
        debut = fin
    return "".join(normalise), positions, debuts_unites, fins_unites


def _syllabe_hangul_sans_final(caractere: str) -> bool:
    return "가" <= caractere <= "힣" and (ord(caractere) - ord("가")) % 28 == 0


def _jamo_initial(caractere: str) -> bool:
    return "ᄀ" <= caractere <= "ᅟ" or "ꥠ" <= caractere <= "ꥼ"


def _jamo_medial(caractere: str) -> bool:
    return "ᅠ" <= caractere <= "ᆧ" or "ힰ" <= caractere <= "ퟆ"


def _jamo_final(caractere: str) -> bool:
    return "ᆨ" <= caractere <= "ᇿ" or "ퟋ" <= caractere <= "ퟻ"


def _frontiere(texte: str, debut: int, fin: int) -> bool:
    return not (
        (debut > 0 and _caractere_de_mot(texte[debut - 1]))
        or (fin < len(texte) and _caractere_de_mot(texte[fin]))
    )


def _caractere_de_mot(caractere: str) -> bool:
    return caractere == "_" or unicodedata.category(caractere)[0] in {"L", "N", "M"}


def _fusionner(intervalles: list[tuple[int, int]]) -> list[tuple[int, int]]:
    resultat: list[tuple[int, int]] = []
    for debut, fin in sorted(intervalles):
        if resultat and debut <= resultat[-1][1]:
            resultat[-1] = (resultat[-1][0], max(resultat[-1][1], fin))
        else:
            resultat.append((debut, fin))
    return resultat


def _morceau_utile(texte: str, debut: int, fin: int) -> list[tuple[int, int]]:
    while debut < fin and texte[debut].isspace():
        debut += 1
    while fin > debut and texte[fin - 1].isspace():
        fin -= 1
    return (
        [(debut, fin)]
        if debut < fin and any(c.isalnum() for c in texte[debut:fin])
        else []
    )
