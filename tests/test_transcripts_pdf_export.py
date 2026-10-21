from datetime import date, datetime
from io import BytesIO

from pypdf import PdfReader

from transcripts_pdf.depot import SourceTranscriptPdf
from transcripts_pdf.export import generer_pdf


def _source(contenu: str, contexte: str = "") -> SourceTranscriptPdf:
    return SourceTranscriptPdf(
        12,
        "bizdev",
        4,
        "entretien.pdf",
        date(2026, 10, 19),
        contenu,
        contexte,
        [
            {
                "identifiant": "SPEAKER_01",
                "role": "externe",
                "nom_affiche": "Élodie œuf",
                "justification": "Ne doit pas apparaître.",
            },
            {
                "identifiant": "SPEAKER_02",
                "role": "externe",
                "nom_affiche": "",
                "justification": "Ne doit pas apparaître.",
            },
        ],
        datetime(2026, 10, 19),
    )


def test_generer_pdf_contient_le_transcript_et_le_contexte_pseudonymises() -> None:
    source = _source(
        "SPEAKER_01: Élodie parle d’œufs — « l’équipe » & <script>\n"
        "SPEAKER_02: Participant identifié.\nSPEAKER_03: Participant inconnu.",
        "Contexte avec œ et apostrophe typographique ’.",
    )
    lecteur = PdfReader(BytesIO(generer_pdf(source)))
    texte = "\n".join(page.extract_text() or "" for page in lecteur.pages)
    assert "Transcript pseudonymisé" in texte
    assert "BizDev" in texte
    assert "19/10/2026" in texte
    assert "Élodie œuf : Élodie parle d’œufs" in texte
    assert "« l’équipe » & <script>" in texte
    assert "Externe · 2 : Participant identifié." in texte
    assert "SPEAKER_03: Participant inconnu." in texte
    assert "Contexte avec œ et apostrophe typographique ’." in texte
    assert "Ne doit pas apparaître" not in texte


def test_generer_pdf_repartit_le_transcript_entier_sur_plusieurs_pages() -> None:
    lecteur = PdfReader(
        BytesIO(
            generer_pdf(_source("Début " + "mot central " * 1600 + "Fin transcript."))
        )
    )
    texte = " ".join(page.extract_text() or "" for page in lecteur.pages)
    assert len(lecteur.pages) > 1
    assert "Début" in texte
    assert "mot central" in texte
    assert "Fin transcript." in texte
