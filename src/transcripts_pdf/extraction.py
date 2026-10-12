from datetime import date
from io import BytesIO
from pathlib import Path
import re

from pypdf import PdfReader

TAILLE_MAXIMALE = 10 * 1024 * 1024
PAGES_MAXIMALES = 50
CARACTERES_MAXIMAUX = 100_000


class ErreurPdf(ValueError):
    pass


def extraire_pdf(nom_fichier: str, contenu: bytes) -> tuple[str, date | None]:
    if len(contenu) > TAILLE_MAXIMALE:
        raise ErreurPdf("Le fichier dépasse 10 Mo.")
    try:
        lecteur = PdfReader(BytesIO(contenu))
        if lecteur.is_encrypted:
            raise ErreurPdf("Les PDF chiffrés ne sont pas pris en charge.")
        if len(lecteur.pages) > PAGES_MAXIMALES:
            raise ErreurPdf("Le PDF dépasse 50 pages.")
        pages = [page.extract_text() or "" for page in lecteur.pages]
    except ErreurPdf:
        raise
    except Exception as erreur:
        raise ErreurPdf("Le PDF est illisible.") from erreur
    if any(not page.strip() for page in pages):
        raise ErreurPdf("Le PDF contient une page sans texte extractible.")
    texte = "\n".join(pages)
    texte = re.sub(
        r"(?im)^\s*T[eé]l[eé]charger votre enregistrement(?: audio)?(?:\s*\(lien externe\))?\s*$",
        "",
        texte,
    ).strip()
    if not texte:
        raise ErreurPdf("Le PDF ne contient pas de texte extractible.")
    if len(texte) > CARACTERES_MAXIMAUX:
        raise ErreurPdf("Le texte du PDF dépasse 100 000 caractères.")
    date_match = re.search(
        r"-du-(\d{4}-\d{2}-\d{2})-a-\d{2}_\d{2}", Path(nom_fichier).stem
    )
    try:
        date_source = date.fromisoformat(date_match[1]) if date_match else None
    except ValueError:
        date_source = None
    return texte, date_source


def anonymiser_locuteurs(texte: str) -> tuple[str, list[tuple[str, str]]]:
    labels = list(
        dict.fromkeys(re.findall(r"(?m)^([A-Za-z]{7}_[0-9]{2}|None):\s+", texte))
    )
    suffixes = [label[-2:] for label in labels]
    if len(set(suffixes)) != len(suffixes):
        raise ErreurPdf("Les identifiants de locuteur sont ambigus.")
    if "None" in labels:
        disponible = next(
            (
                f"{suffixe:02d}"
                for suffixe in range(100)
                if f"{suffixe:02d}" not in suffixes
            ),
            None,
        )
        if disponible is None:
            raise ErreurPdf("Les identifiants de locuteur sont ambigus.")
        locuteurs = {label: f"SPEAKER_{label[-2:]}" for label in set(labels) - {"None"}}
        locuteurs["None"] = f"SPEAKER_{disponible}"
    else:
        locuteurs = {label: f"SPEAKER_{label[-2:]}" for label in labels}
    for label, anonyme in locuteurs.items():
        texte = texte.replace(label + ":", anonyme + ":")
    return texte, list(locuteurs.items())


def appliquer_remplacements(texte: str, remplacements: list[tuple[str, str]]) -> str:
    remplacements_tries = sorted(remplacements, key=lambda item: -len(item[0]))
    valeurs = {original: anonymise for original, anonymise in remplacements_tries}
    motif = re.compile("|".join(re.escape(original) for original in valeurs))
    return motif.sub(lambda match: valeurs[match[0]], texte) if valeurs else texte


def appliquer_remplacements_positions(
    texte: str, remplacements: list[tuple[int, int, str]]
) -> str:
    fin_precedente = len(texte)
    for debut, fin, valeur in sorted(remplacements, reverse=True):
        if debut < 0 or fin <= debut or fin > fin_precedente:
            raise ValueError("Les positions de remplacement se chevauchent.")
        texte = texte[:debut] + valeur + texte[fin:]
        fin_precedente = debut
    return texte
