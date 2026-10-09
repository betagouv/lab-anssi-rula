import json

from io import BytesIO

from datetime import date, datetime, timedelta

from typing import Any, cast


import pytest

from pypdf import PdfWriter


from tests.adaptateurs.albert_de_test import AdaptateurAlbertDeTest

from infra.memoire.depot_transcripts_pdf import DepotTranscriptsPdfMemoire

from transcripts_pdf.extraction import ErreurPdf, appliquer_remplacements, extraire_pdf

from transcripts_pdf.extraction import anonymiser_locuteurs

from transcripts_pdf.service import (
    Remplacement,
    ServicePreparationTranscript,
    _decouper,
)


def _pdf(*pages: str) -> bytes:

    objets = [b"<< /Type /Catalog /Pages 2 0 R >>", b""]

    police_id = 3 + len(pages) * 2

    for index, page in enumerate(pages):
        page_id = 3 + index * 2

        flux_id = page_id + 1

        flux = f"BT /F1 12 Tf 40 750 Td ({page}) Tj ET".encode()

        objets.extend(
            [
                f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 600 800] /Resources << /Font << /F1 {police_id} 0 R >> >> /Contents {flux_id} 0 R >>".encode(),
                b"<< /Length "
                + str(len(flux)).encode()
                + b" >>\nstream\n"
                + flux
                + b"\nendstream",
            ]
        )

    objets[1] = (
        f"<< /Type /Pages /Kids [{' '.join(f'{3 + i * 2} 0 R' for i in range(len(pages)))}] /Count {len(pages)} >>".encode()
    )

    objets.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

    sortie = bytearray(b"%PDF-1.4\n")

    offsets = [0]

    for identifiant, objet in enumerate(objets, 1):
        offsets.append(len(sortie))

        sortie.extend(f"{identifiant} 0 obj\n".encode() + objet + b"\nendobj\n")

    debut_xref = len(sortie)

    sortie.extend(f"xref\n0 {len(offsets)}\n0000000000 65535 f \n".encode())

    for offset in offsets[1:]:
        sortie.extend(f"{offset:010d} 00000 n \n".encode())

    sortie.extend(
        f"trailer\n<< /Size {len(offsets)} /Root 1 0 R >>\nstartxref\n{debut_xref}\n%%EOF".encode()
    )

    return bytes(sortie)


def test_extraire_pdf_conserve_toutes_les_pages_et_date_du_nom() -> None:

    contenu, date_source = extraire_pdf(
        "entretien-du-2026-04-07-a-10_34.pdf",
        _pdf("Premiere page", "Suite page suivante"),
    )

    assert contenu == "Premiere page\nSuite page suivante"

    assert date_source is not None

    assert date_source.isoformat() == "2026-04-07"


def test_extraire_pdf_ignore_date_invalide_et_retire_bandeau() -> None:

    contenu, date_source = extraire_pdf(
        "entretien-du-2026-02-31-a-10_34.pdf",
        _pdf("Telecharger votre enregistrement (lien externe)", "Texte utile"),
    )

    assert contenu == "Texte utile"

    assert date_source is None


def test_extraire_pdf_refuse_pdf_chiffre_et_trop_de_pages() -> None:

    chiffre = PdfWriter()

    chiffre.add_blank_page(width=100, height=100)

    chiffre.encrypt("secret")

    flux = BytesIO()

    chiffre.write(flux)

    with pytest.raises(ErreurPdf, match="chiffr"):
        extraire_pdf("chiffre.pdf", flux.getvalue())

    with pytest.raises(ErreurPdf, match="50 pages"):
        extraire_pdf("long.pdf", _pdf(*(f"page {index}" for index in range(51))))

    with pytest.raises(ErreurPdf, match="pas de texte extractible"):
        extraire_pdf(
            "bandeau.pdf", _pdf("Telecharger votre enregistrement (lien externe)")
        )


@pytest.mark.parametrize(
    "nom,contenu,attendu",
    [
        ("fichier.pdf", b"pas un PDF", "illisible"),
        ("fichier.pdf", _pdf(""), "page sans texte"),
        ("fichier.pdf", _pdf("x" * 100_001), "100 000"),
        ("fichier.pdf", b"x" * (10 * 1024 * 1024 + 1), "10 Mo"),
    ],
    ids=["illisible", "page_vide", "trop_long", "trop_lourd"],
)
def test_extraire_pdf_refuse_les_limites_et_le_texte_non_extractible(
    nom: str, contenu: bytes, attendu: str
) -> None:

    with pytest.raises(ErreurPdf, match=attendu):
        extraire_pdf(nom, contenu)


def test_anonymiser_locuteurs_preserve_suffixes_et_tours_interpages() -> None:

    contenu, locuteurs = anonymiser_locuteurs(
        "Entretien\nLocutrr_07: Premier tour\nSuite page\nAutreXX_02: Autre tour"
    )

    assert (
        contenu
        == "Entretien\nSPEAKER_07: Premier tour\nSuite page\nSPEAKER_02: Autre tour"
    )

    assert set(locuteurs) == {
        ("Locutrr_07", "SPEAKER_07"),
        ("AutreXX_02", "SPEAKER_02"),
    }


def test_anonymiser_locuteur_inconnu_none_sans_fusionner_les_tours() -> None:

    contenu, locuteurs = anonymiser_locuteurs(
        "None: Tour inconnu\nLocutrr_01: Tour connu"
    )

    assert contenu == "SPEAKER_00: Tour inconnu\nSPEAKER_01: Tour connu"

    assert set(locuteurs) == {("None", "SPEAKER_00"), ("Locutrr_01", "SPEAKER_01")}


def test_anonymiser_locuteurs_refuse_suffixes_ambigus() -> None:

    with pytest.raises(ErreurPdf, match="ambigus"):
        anonymiser_locuteurs("Locutrr_07: A\nSpeaker_07: B")


def test_anonymiser_locuteurs_refuse_si_aucun_identifiant_libre_ne_reste() -> None:

    texte = "\n".join([*(f"Speaker_{index:02d}: X" for index in range(100)), "None: Y"])

    with pytest.raises(ErreurPdf, match="ambigus"):
        anonymiser_locuteurs(texte)


def test_appliquer_remplacements_ne_cascade_pas_et_choisit_la_plus_longue() -> None:

    assert appliquer_remplacements("A B", [("A", "B"), ("B", "C"), ("A B", "D")]) == "D"

    assert appliquer_remplacements("A B", [("A", "B"), ("B", "C")]) == "B C"

    assert appliquer_remplacements("aucun remplacement", []) == "aucun remplacement"


def test_appliquer_positions_refuse_des_indices_invalides() -> None:

    from transcripts_pdf.extraction import appliquer_remplacements_positions

    with pytest.raises(ValueError, match="chevauchent"):
        appliquer_remplacements_positions("texte", [(0, 9, "x"), (3, 5, "y")])


def test_preparation_anonymise_locuteurs_et_applique_remplacements_en_python() -> None:

    albert = AdaptateurAlbertDeTest().avec_reponse(
        json.dumps(
            {
                "remplacements": [
                    {
                        "valeur": "Alice",
                        "categorie": "identite",
                        "champ": "transcript",
                    },
                    {
                        "valeur": "Alice",
                        "categorie": "identite",
                        "champ": "contexte",
                    },
                ],
                "locuteurs": [
                    {
                        "speaker_id": "SPEAKER_01",
                        "role": "externe",
                        "justification": "Alice est participante externe.",
                    }
                ],
            }
        )
    )

    service = ServicePreparationTranscript(albert, "prompt")

    preparation = service.preparer(
        "reunion-_zbq-okak-bsa_-du-2026-04-07-a-10_34.pdf",
        _pdf("Locutrr_01: Alice veut exporter."),
        "produit",
        "Contexte Alice",
    )

    assert preparation.contenu == "SPEAKER_01: [IDENTITE_01] veut exporter."

    assert preparation.contexte == "Contexte [IDENTITE_01]"

    assert preparation.locuteurs[0].identifiant == "SPEAKER_01"

    assert (
        preparation.locuteurs[0].justification
        == "Les extraits indiquent un rôle externe."
    )

    assert preparation.nom_source == "reunion-_zbq-okak-bsa_-du-2026-04-07-a-10_34.pdf"


def test_preparation_refuse_un_remplacement_absent_du_groupe_source() -> None:

    reponse = json.dumps(
        {
            "remplacements": [
                {"valeur": "Alice", "categorie": "identite", "champ": "transcript"}
            ],
            "locuteurs": [
                {
                    "speaker_id": "SPEAKER_01",
                    "role": "externe",
                    "justification": "RÃ´le externe.",
                }
            ],
        }
    )

    service = ServicePreparationTranscript(
        AdaptateurAlbertDeTest().avec_reponse(reponse), "prompt"
    )

    with pytest.raises(ValueError, match="invalide"):
        service.preparer(
            "reunion.pdf",
            _pdf("Speaker_01: " + "x" * 2300, "Speaker_02: Alice"),
            "produit",
            "",
        )


def test_preparation_refuse_reponse_de_locuteur_inconnu() -> None:

    albert = AdaptateurAlbertDeTest().avec_reponse(
        json.dumps(
            {
                "remplacements": [],
                "locuteurs": [
                    {
                        "speaker_id": "SPEAKER_02",
                        "role": "interne",
                        "justification": "RÃ´le interne.",
                    }
                ],
            }
        )
    )

    service = ServicePreparationTranscript(albert, "prompt")

    with pytest.raises(ValueError, match="invalide"):
        service.preparer("reunion.pdf", _pdf("Locutrr_01: Bonjour"), "produit", "")


@pytest.mark.parametrize(
    "reponse",
    [
        "pas-json",
        "{}",
        '{"remplacements":{},"locuteurs":[]}',
        '{"remplacements":[{"valeur":"Alice","categorie":"identite","champ":"autre"}],"locuteurs":[]}',
        '{"remplacements":[],"locuteurs":[{"libelle":"Speaker_01","role":"autre","justification":"x"}]}',
    ],
)
def test_preparation_refuse_une_reponse_de_modele_mal_formee(reponse: str) -> None:

    service = ServicePreparationTranscript(
        AdaptateurAlbertDeTest().avec_reponse(reponse), "prompt"
    )

    with pytest.raises(ValueError, match="invalide"):
        service.preparer("reunion.pdf", _pdf("Speaker_01: Texte"), "produit", "")


def test_preparation_accepte_un_role_indetermine() -> None:

    service = ServicePreparationTranscript(
        AdaptateurAlbertDeTest().avec_reponse(
            json.dumps(
                {
                    "remplacements": [],
                    "locuteurs": [
                        {
                            "speaker_id": "SPEAKER_01",
                            "role": "indetermine",
                            "justification": "Non Ã©tabli.",
                        }
                    ],
                }
            )
        ),
        "prompt",
    )

    resultat = service.preparer(
        "reunion.pdf", _pdf("Speaker_01: Bonjour"), "produit", ""
    )

    assert resultat.locuteurs[0].role == "indetermine"


def test_schema_locuteurs_force_chaque_identifiant_transmis() -> None:

    from transcripts_pdf.service import _lire_preparation, _schema_preparation

    schema = _schema_preparation({"SPEAKER_01", "SPEAKER_02"})

    proprietes = cast(dict[str, Any], schema["properties"])

    locuteurs = cast(dict[str, Any], proprietes["locuteurs"])

    assert locuteurs["required"] == ["SPEAKER_01", "SPEAKER_02"]

    assert _lire_preparation(
        json.dumps(
            {
                "remplacements": [],
                "locuteurs": {
                    "SPEAKER_01": {"role": "interne", "justification": "RÃ´le interne."}
                },
            }
        )
    )["locuteurs"] == [
        {
            "speaker_id": "SPEAKER_01",
            "role": "interne",
            "justification": "RÃ´le interne.",
        }
    ]

    with pytest.raises(ValueError, match="invalide"):
        _lire_preparation('{"remplacements": [], "locuteurs": "invalides"}')


def test_preparation_refuse_un_type_de_source_invalide() -> None:

    service = ServicePreparationTranscript(AdaptateurAlbertDeTest(), "prompt")

    with pytest.raises(ValueError, match="Type de source invalide"):
        service.preparer("reunion.pdf", b"", "ux", "")


def test_decoupage_preserve_les_tours_et_tous_les_caracteres() -> None:

    texte = "Speaker_01: " + "mot " * 1100 + "\nSpeaker_02: " + "mot " * 1000

    segments = _decouper(texte, par_tour=True)

    from transcripts_pdf.service import _fragments_transcript

    fragments = _fragments_transcript(
        "PrÃ©ambule\nSpeaker_01: Bonjour", {"Speaker_01": "SPEAKER_01"}
    )

    assert fragments[0].speaker_id is None

    assert len(segments) > 1

    assert all(len(segment) <= 2000 for segment in segments)

    assert "".join(segments) == texte

    contexte = "Contexte " * 1000

    segments_contexte = _decouper(contexte)

    assert len(segments_contexte) > 1

    assert all(len(segment) <= 2000 for segment in segments_contexte)

    assert "".join(segments_contexte) == contexte


def test_decoupage_consolide_un_role_incoherent_en_indetermine() -> None:

    reponses = [
        json.dumps(
            {
                "remplacements": [],
                "locuteurs": [
                    {
                        "speaker_id": "SPEAKER_01",
                        "role": "externe",
                        "justification": "Le rÃ´le semble externe.",
                    }
                ],
            }
        ),
        json.dumps(
            {
                "remplacements": [],
                "locuteurs": [
                    {
                        "speaker_id": "SPEAKER_01",
                        "role": "interne",
                        "justification": "Le rÃ´le semble interne.",
                    }
                ],
            }
        ),
    ]

    service = ServicePreparationTranscript(
        AdaptateurAlbertDeTest().avec_reponses(reponses * 10), "prompt"
    )

    resultat = service.preparer(
        "reunion.pdf",
        _pdf("Speaker_01: " + "mot " * 1100, "Speaker_01: " + "autre " * 900),
        "produit",
        "",
    )

    assert resultat.locuteurs[0].role == "indetermine"

    assert (
        resultat.locuteurs[0].justification
        == "Les extraits ne permettent pas de d\u00e9terminer le r\u00f4le."
    )


@pytest.mark.parametrize(
    "remplacements,texte,contexte,attendu",
    [
        (
            [{"valeur": "Alice", "categorie": "identite", "champ": "transcript"}],
            "Alice voit Alice",
            "",
            "[IDENTITE_01] voit [IDENTITE_01]",
        ),
        (
            [
                {"valeur": "Alice", "categorie": "identite", "champ": "transcript"},
                {"valeur": "Alice", "categorie": "identite", "champ": "transcript"},
            ],
            "Alice",
            "",
            "[IDENTITE_01]",
        ),
        (
            [
                {"valeur": "Alice", "categorie": "identite", "champ": "transcript"},
                {"valeur": "Alice", "categorie": "organisation", "champ": "transcript"},
            ],
            "Alice",
            "",
            "invalide",
        ),
        (
            [
                {
                    "valeur": "Alice Dupont",
                    "categorie": "identite",
                    "champ": "transcript",
                },
                {"valeur": "Alice", "categorie": "identite", "champ": "transcript"},
            ],
            "Alice Dupont",
            "",
            "[IDENTITE_01]",
        ),
        (
            [{"valeur": "Alice", "categorie": "identite", "champ": "transcript"}],
            "Bob",
            "",
            "invalide",
        ),
    ],
)
def test_positions_python_repeated_duplicate_conflict_overlap_and_absence(
    remplacements: list[Remplacement],
    texte: str,
    contexte: str,
    attendu: str,
) -> None:

    from transcripts_pdf.service import _positions_valides

    if attendu == "invalide":
        with pytest.raises(ValueError, match="invalide|incompatibles|plusieurs"):
            _positions_valides(remplacements, texte, contexte)

    else:
        positions = _positions_valides(remplacements, texte, contexte)

        from transcripts_pdf.extraction import appliquer_remplacements_positions

        resultat = appliquer_remplacements_positions(
            texte,
            [(debut, fin, "[IDENTITE_01]") for _, debut, fin in positions],
        )

        assert resultat == attendu


def test_positions_refusent_un_chevauchement_partiel_de_categories() -> None:

    from transcripts_pdf.service import _positions_valides

    with pytest.raises(ValueError, match="incompatibles"):
        _positions_valides(
            [
                {"valeur": "Alice", "categorie": "identite", "champ": "transcript"},
                {
                    "valeur": "lice B",
                    "categorie": "organisation",
                    "champ": "transcript",
                },
            ],
            "Alice B",
            "",
        )

    with pytest.raises(ValueError, match="se chevauchent"):
        _positions_valides(
            [
                {"valeur": "Alice", "categorie": "identite", "champ": "transcript"},
                {"valeur": "lice B", "categorie": "identite", "champ": "transcript"},
            ],
            "Alice B",
            "",
        )


def test_positions_rejettent_une_valeur_vide() -> None:

    from transcripts_pdf.service import _positions_valides

    with pytest.raises(ValueError, match="invalide"):
        _positions_valides(
            [{"valeur": "", "categorie": "identite", "champ": "transcript"}],
            "texte",
            "",
        )


def test_job_refuse_un_ancien_jeton_apres_reprise_de_bail() -> None:

    depot = DepotTranscriptsPdfMemoire()

    source = depot.ajouter(
        "bizdev", 1, None, "source.pdf", date.today(), "SPEAKER_01: Texte", "", []
    )

    job = depot.creer_job(source.id)

    ancien = depot.reclamer_job(job.id)

    assert ancien is not None

    depot.jobs[0] = ancien._replace(bail_jusqua=datetime.now() - timedelta(seconds=1))

    courant = depot.reclamer_job(job.id)

    assert courant is not None

    assert courant.jeton != ancien.jeton

    assert not depot.finaliser(ancien, {"resume": "ancien"}, [], "v1", "v1")

    assert depot.finaliser(courant, {"resume": "courant"}, [], "v1", "v1")


def test_job_refuse_la_finalisation_apres_modification_du_transcript() -> None:

    depot = DepotTranscriptsPdfMemoire()

    source = depot.ajouter(
        "bizdev", 1, None, "source.pdf", date.today(), "SPEAKER_01: Texte", "", []
    )

    job = depot.reclamer_job(depot.creer_job(source.id).id)

    assert job is not None

    depot.modifier(source.id, date.today(), "SPEAKER_01: ModifiÃ©", "", [])

    assert not depot.finaliser(job, {"resume": "obsolÃ¨te"}, [], "v1", "v1")


def test_depot_memoire_signale_une_source_et_un_job_absents() -> None:

    depot = DepotTranscriptsPdfMemoire()

    assert depot.modifier(99, date.today(), "texte", "", []) is None

    with pytest.raises(ValueError, match="introuvable"):
        depot.creer_job(99)
