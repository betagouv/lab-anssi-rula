from html import escape
from io import BytesIO
from pathlib import Path
import re

from reportlab import __file__ as reportlab_fichier
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Flowable, Paragraph, SimpleDocTemplate

from transcripts_pdf.depot import SourceTranscriptPdf

_POLICE = "RulaVera"
_POLICE_FICHIER = Path(reportlab_fichier).parent / "fonts" / "Vera.ttf"
pdfmetrics.registerFont(TTFont(_POLICE, str(_POLICE_FICHIER)))
_ROLES = {"interne": "Interne", "externe": "Externe", "indetermine": "Indéterminé"}


def _contenu_avec_locuteurs(source: SourceTranscriptPdf) -> str:
    locuteurs = {locuteur["identifiant"]: locuteur for locuteur in source.locuteurs}

    def remplacer(correspondance: re.Match[str]) -> str:
        identifiant = correspondance[0][:-1]
        locuteur = locuteurs.get(identifiant)
        if locuteur is None:
            return identifiant + ":"
        nom = locuteur.get("nom_affiche", "").strip()
        numero = str(int(identifiant.rsplit("_", maxsplit=1)[1]))
        return f"{nom or _ROLES.get(locuteur['role'], 'Indéterminé') + ' · ' + numero} :"

    return re.sub(r"SPEAKER_\d{2}:", remplacer, source.contenu)


def _paragraphe(texte: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(escape(texte).replace("\n", "<br/>"), style)


def generer_pdf(source: SourceTranscriptPdf) -> bytes:
    tampon = BytesIO()
    styles = getSampleStyleSheet()
    titre = ParagraphStyle(
        "TitreTranscript",
        parent=styles["Title"],
        fontName=_POLICE,
        fontSize=19,
        leading=24,
        alignment=TA_LEFT,
        textColor=HexColor("#161616"),
        spaceAfter=8,
    )
    metadonnees = ParagraphStyle(
        "MetadonneesTranscript",
        parent=styles["Normal"],
        fontName=_POLICE,
        fontSize=10,
        leading=15,
        textColor=HexColor("#666666"),
        spaceAfter=24,
    )
    rubrique = ParagraphStyle(
        "RubriqueTranscript",
        parent=styles["Heading2"],
        fontName=_POLICE,
        fontSize=12,
        leading=16,
        textColor=HexColor("#161616"),
        spaceBefore=12,
        spaceAfter=8,
        keepWithNext=True,
    )
    texte = ParagraphStyle(
        "TexteTranscript",
        parent=styles["BodyText"],
        fontName=_POLICE,
        fontSize=9.5,
        leading=14,
        textColor=HexColor("#161616"),
        splitLongWords=True,
        wordWrap="CJK",
        spaceAfter=8,
    )
    document = SimpleDocTemplate(
        tampon,
        pagesize=A4,
        leftMargin=54,
        rightMargin=54,
        topMargin=56,
        bottomMargin=48,
        title="Transcript pseudonymisé",
    )
    type_source = "Produit" if source.type_source == "produit" else "BizDev"
    date_entretien = (
        source.date_entretien.strftime("%d/%m/%Y")
        if source.date_entretien
        else "Non renseignée"
    )
    contenu = _contenu_avec_locuteurs(source)
    elements: list[Flowable] = [
        _paragraphe("Transcript pseudonymisé", titre),
        _paragraphe(f"{type_source} · {date_entretien}", metadonnees),
        _paragraphe("Transcript", rubrique),
        _paragraphe(contenu, texte),
    ]
    if source.contexte:
        elements.extend(
            [
                _paragraphe("Contexte", rubrique),
                _paragraphe(source.contexte, texte),
            ]
        )
    document.build(elements)
    return tampon.getvalue()
