import json
import logging

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
    ErreurPreparationInvalide,
    ServicePreparationTranscript,
    _decouper,
    _lire_preparation,
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


def _reponses_preparation(
    texte: str,
    contexte: str = "",
    detections: list[tuple[str, str, str]] | None = None,
    roles: dict[str, str] | None = None,
) -> list[str]:
    from transcripts_pdf.service import (
        _fragments_champ,
        _fragments_transcript,
        _grouper_fragments,
        _tokeniser,
    )

    texte, _ = extraire_pdf("reunion.pdf", _pdf(texte))
    identifiants = dict(anonymiser_locuteurs(texte)[1])
    fragments = [
        fragment._replace(fragment_id=index)
        for index, fragment in enumerate(
            _fragments_transcript(texte, identifiants)
            + (_fragments_champ("contexte", contexte) if contexte else []),
            1,
        )
    ]
    groupes = _grouper_fragments(fragments)
    roles = roles or {}
    remplacements_par_groupe: list[list[dict[str, object]]] = [[] for _ in groupes]
    for champ, valeur, categorie in detections or []:
        for index, groupe in enumerate(groupes):
            fragment = next(
                (
                    fragment
                    for fragment in groupe
                    if fragment.champ == champ and valeur in fragment.contenu
                ),
                None,
            )
            if fragment is None:
                continue
            debut = fragment.contenu.index(valeur)
            fin = debut + len(valeur)
            tokens = _tokeniser(fragment.contenu)
            token_debut = next(
                token_id for token_id, token in enumerate(tokens) if token[1] == debut
            )
            token_fin = next(
                token_id for token_id, token in enumerate(tokens) if token[2] == fin
            )
            remplacements_par_groupe[index].append(
                {
                    "categorie": categorie,
                    "fragment_id": fragment.fragment_id,
                    "token_debut": token_debut,
                    "token_fin": token_fin,
                }
            )
            break
    reponses = []
    for groupe, remplacements in zip(groupes, remplacements_par_groupe, strict=True):
        speakers = {
            fragment.speaker_id
            for fragment in groupe
            if fragment.champ == "transcript" and fragment.speaker_id
        }
        reponses.append(
            json.dumps(
                {
                    "remplacements": remplacements,
                    "locuteurs": {
                        speaker_id: {
                            "role": roles.get(speaker_id, "externe"),
                            "justification": "Le fragment identifie un rôle.",
                        }
                        for speaker_id in sorted(speakers)
                    },
                }
            )
        )
    return reponses


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


def test_preparation_anonymise_locuteurs_et_applique_remplacements_en_python(
    caplog,
) -> None:
    caplog.set_level(logging.INFO, logger="uvicorn.error")

    albert = AdaptateurAlbertDeTest().avec_reponses(
        _reponses_preparation(
            "Locutrr_01: Alice veut exporter.",
            "Contexte Alice",
            [("transcript", "Alice", "identite"), ("contexte", "Alice", "identite")],
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
    assert "'phase': 'groupe'" in caplog.text


def test_preparation_journalise_un_echec_sans_message_exception(caplog) -> None:
    caplog.set_level(logging.INFO, logger="uvicorn.error")
    service = ServicePreparationTranscript(
        AdaptateurAlbertDeTest().avec_erreur(RuntimeError("texte privé")), "prompt"
    )

    with pytest.raises(RuntimeError, match="texte privé"):
        service.preparer("reunion.pdf", _pdf("Speaker_01: Texte"), "produit", "")

    assert "Diagnostic préparation transcript" in caplog.text
    assert "RuntimeError" in caplog.text
    assert "texte privé" not in caplog.text


def test_preparation_journalise_une_erreur_de_fusion_sans_valeurs_source(caplog):
    caplog.set_level(logging.INFO, logger="uvicorn.error")
    reponses = _reponses_preparation(
        "Speaker_01: " + "x" * 1940 + " Alice " + "y" * 250,
        detections=[
            ("transcript", "Alice", "identite"),
            ("transcript", "Alice", "organisation"),
        ],
    )
    service = ServicePreparationTranscript(
        AdaptateurAlbertDeTest().avec_reponses(reponses), "prompt"
    )

    with pytest.raises(ValueError, match="plusieurs catégories"):
        service.preparer(
            "reunion.pdf",
            _pdf("Speaker_01: " + "x" * 1940 + " Alice " + "y" * 250),
            "produit",
            "",
        )

    assert "'phase': 'fusion_finale'" in caplog.text
    assert "'code_validation': 'categories_incompatibles'" in caplog.text
    assert "Alice" not in caplog.text


def test_preparation_refuse_un_index_de_token_absent_du_groupe(caplog) -> None:
    caplog.set_level(logging.INFO, logger="uvicorn.error")

    reponse = json.dumps(
        {
            "remplacements": [
                {
                    "categorie": "identite",
                    "fragment_id": 1,
                    "token_debut": 9999,
                    "token_fin": 9999,
                }
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

    with pytest.raises(ErreurPreparationInvalide, match="invalide") as erreur:
        service.preparer(
            "reunion.pdf",
            _pdf("Speaker_01: Texte"),
            "produit",
            "",
        )
    assert erreur.value.code == "token_absent"
    assert "'code_validation': 'token_absent'" in caplog.text
    assert "'champ': 'tokens'" in caplog.text


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

    with pytest.raises(ErreurPreparationInvalide, match="invalide") as erreur:
        service.preparer("reunion.pdf", _pdf("Locutrr_01: Bonjour"), "produit", "")
    assert erreur.value.code == "ensemble_speakers_inattendu"


@pytest.mark.parametrize(
    ("reponse", "code"),
    [
        ("pas-json", "json_illisible"),
        ("{}", "structure_premier_niveau"),
        ('{"remplacements":{},"locuteurs":[]}', "structure_remplacements"),
        ('{"remplacements":[{}],"locuteurs":[]}', "structure_remplacements"),
        (
            '{"remplacements":[{"valeur":"Alice","categorie":"identite","champ":"transcript"}],"locuteurs":[]}',
            "structure_remplacements",
        ),
        ('{"remplacements":[],"locuteurs":"invalides"}', "structure_locuteurs"),
        ('{"remplacements":[],"locuteurs":[{"foo":"bar"}]}', "structure_locuteurs"),
        (
            '{"remplacements":[],"locuteurs":{"SPEAKER_01":"invalides"}}',
            "structure_locuteurs",
        ),
    ],
)
def test_preparation_classe_les_reponses_non_conformes(reponse: str, code: str) -> None:
    with pytest.raises(ErreurPreparationInvalide) as erreur:
        _lire_preparation(reponse)
    assert erreur.value.code == code


@pytest.mark.parametrize(
    "reponse",
    [
        "pas-json",
        "{}",
        '{"remplacements":{},"locuteurs":[]}',
        '{"remplacements":[{"categorie":"identite","fragment_id":1,"token_debut":0,"token_fin":0}],"locuteurs":[]}',
        '{"remplacements":[{"categorie":"autre","fragment_id":1,"token_debut":0,"token_fin":0}],"locuteurs":[]}',
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
        AdaptateurAlbertDeTest().avec_reponses(
            _reponses_preparation(
                "Speaker_01: Bonjour", roles={"SPEAKER_01": "indetermine"}
            )
        ),
        "prompt",
    )

    resultat = service.preparer(
        "reunion.pdf", _pdf("Speaker_01: Bonjour"), "produit", ""
    )

    assert resultat.locuteurs[0].role == "indetermine"


def test_preparation_emet_une_progression_monotone() -> None:
    texte = "Speaker_01: Alice"
    evenements: list[tuple[str, int, int | None, int | None]] = []
    service = ServicePreparationTranscript(
        AdaptateurAlbertDeTest().avec_reponses(
            _reponses_preparation(
                texte, detections=[("transcript", "Alice", "identite")]
            )
        ),
        "prompt",
    )

    service.preparer(
        "reunion.pdf",
        _pdf(texte),
        "produit",
        "",
        lambda phase, termines, total, actif: evenements.append(
            (phase, termines, total, actif)
        ),
    )

    assert evenements == [
        ("extraction", 0, None, None),
        ("anonymisation", 0, 1, 1),
        ("anonymisation", 1, 1, None),
        ("finalisation", 1, 1, None),
    ]


def test_preparation_ne_compte_pas_le_groupe_en_echec() -> None:
    evenements: list[tuple[str, int, int | None, int | None]] = []
    service = ServicePreparationTranscript(
        AdaptateurAlbertDeTest().avec_erreur(ValueError("réponse privée")), "prompt"
    )

    with pytest.raises(ValueError):
        service.preparer(
            "reunion.pdf",
            _pdf("Speaker_01: Texte"),
            "produit",
            "",
            lambda phase, termines, total, actif: evenements.append(
                (phase, termines, total, actif)
            ),
        )

    assert evenements == [("extraction", 0, None, None), ("anonymisation", 0, 1, 1)]


def test_preparation_ne_transmet_pas_un_fragment_sans_tokens() -> None:
    texte = "Speaker_01: Bonjour"
    resultat = ServicePreparationTranscript(
        AdaptateurAlbertDeTest().avec_reponses(_reponses_preparation(texte, " \n ")),
        "prompt",
    ).preparer("reunion.pdf", _pdf(texte), "produit", " \n ")

    assert resultat.contenu == "SPEAKER_01: Bonjour"
    assert resultat.contexte == " \n "
    assert resultat.locuteurs[0].identifiant == "SPEAKER_01"


def test_schema_locuteurs_force_chaque_identifiant_transmis() -> None:

    from transcripts_pdf.service import (
        _fragments_champ,
        _lire_preparation,
        _schema_preparation,
    )

    fragments = _fragments_champ("transcript", "Alice parle")
    fragments[0] = fragments[0]._replace(fragment_id=7)
    schema = _schema_preparation({"SPEAKER_01", "SPEAKER_02"}, fragments)

    proprietes = cast(dict[str, Any], schema["properties"])

    locuteurs = cast(dict[str, Any], proprietes["locuteurs"])

    assert locuteurs["required"] == ["SPEAKER_01", "SPEAKER_02"]
    remplacements = cast(dict[str, Any], proprietes["remplacements"])
    assert remplacements["items"]["properties"]["fragment_id"]["enum"] == [7]
    assert remplacements["items"]["properties"]["token_debut"]["enum"] == [0, 1]

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
    texte = "Speaker_01: " + "mot " * 1100 + "\nSpeaker_01: " + "autre " * 900
    reponses = _reponses_preparation(texte)
    for index, reponse in enumerate(reponses):
        valeur = json.loads(reponse)
        valeur["locuteurs"]["SPEAKER_01"]["role"] = (
            "externe" if index % 2 == 0 else "interne"
        )
        reponses[index] = json.dumps(valeur)

    service = ServicePreparationTranscript(
        AdaptateurAlbertDeTest().avec_reponses(reponses), "prompt"
    )

    resultat = service.preparer(
        "reunion.pdf",
        _pdf(texte),
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
            [
                {
                    "valeur": "Alice",
                    "categorie": "identite",
                    "champ": "transcript",
                    "debut": 0,
                    "fin": 5,
                }
            ],
            "Alice voit Alice",
            "",
            "[IDENTITE_01] voit Alice",
        ),
        (
            [
                {
                    "valeur": "Alice",
                    "categorie": "identite",
                    "champ": "transcript",
                    "debut": 0,
                    "fin": 5,
                },
                {
                    "valeur": "Alice",
                    "categorie": "identite",
                    "champ": "transcript",
                    "debut": 0,
                    "fin": 5,
                },
            ],
            "Alice",
            "",
            "[IDENTITE_01]",
        ),
        (
            [
                {
                    "valeur": "Alice",
                    "categorie": "identite",
                    "champ": "transcript",
                    "debut": 0,
                    "fin": 5,
                },
                {
                    "valeur": "Alice",
                    "categorie": "organisation",
                    "champ": "transcript",
                    "debut": 0,
                    "fin": 5,
                },
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
                    "debut": 0,
                    "fin": 12,
                },
                {
                    "valeur": "Alice",
                    "categorie": "identite",
                    "champ": "transcript",
                    "debut": 0,
                    "fin": 5,
                },
            ],
            "Alice Dupont",
            "",
            "[IDENTITE_01]",
        ),
        (
            [
                {
                    "valeur": "Alice",
                    "categorie": "identite",
                    "champ": "transcript",
                    "debut": 0,
                    "fin": 3,
                }
            ],
            "Bob",
            "",
            "invalide",
        ),
    ],
)
def test_positions_python_repeated_duplicate_conflict_overlap_and_absence(
    remplacements: list[dict[str, object]],
    texte: str,
    contexte: str,
    attendu: str,
) -> None:

    from transcripts_pdf.service import _positions_valides

    if attendu == "invalide":
        with pytest.raises(ValueError, match="invalide|incompatibles|plusieurs"):
            _positions_valides(cast(Any, remplacements), texte, contexte)

    else:
        positions = _positions_valides(cast(Any, remplacements), texte, contexte)

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
            cast(
                Any,
                [
                    {
                        "valeur": "Alice",
                        "categorie": "identite",
                        "champ": "transcript",
                        "debut": 0,
                        "fin": 5,
                    },
                    {
                        "valeur": "lice B",
                        "categorie": "organisation",
                        "champ": "transcript",
                        "debut": 1,
                        "fin": 7,
                    },
                ],
            ),
            "Alice B",
            "",
        )

    with pytest.raises(ValueError, match="se chevauchent"):
        _positions_valides(
            cast(
                Any,
                [
                    {
                        "valeur": "Alice",
                        "categorie": "identite",
                        "champ": "transcript",
                        "debut": 0,
                        "fin": 5,
                    },
                    {
                        "valeur": "lice B",
                        "categorie": "identite",
                        "champ": "transcript",
                        "debut": 1,
                        "fin": 7,
                    },
                ],
            ),
            "Alice B",
            "",
        )


def test_positions_rejettent_une_valeur_vide() -> None:

    from transcripts_pdf.service import _positions_valides

    with pytest.raises(ValueError, match="invalide"):
        _positions_valides(
            [
                {
                    "valeur": "",
                    "categorie": "identite",
                    "champ": "transcript",
                    "debut": 0,
                    "fin": 0,
                }
            ],
            "texte",
            "",
        )


def test_remplacement_par_tokens_preserve_les_octets_logiques_unicode_et_espaces() -> (
    None
):
    from transcripts_pdf.service import Fragment, _resoudre_remplacements

    texte = "Élodie  d'Arc\nà Paris"
    fragment = Fragment("transcript", 17, texte, offset_debut=23)
    positions = _resoudre_remplacements(
        [
            {
                "categorie": "identite",
                "fragment_id": 17,
                "token_debut": 0,
                "token_fin": 3,
            }
        ],
        [fragment],
    )

    assert positions == [
        {
            "valeur": "Élodie  d'Arc",
            "categorie": "identite",
            "champ": "transcript",
            "debut": 23,
            "fin": 36,
        }
    ]


@pytest.mark.parametrize(
    "fragment_id,token_debut,token_fin,code",
    [(99, 0, 0, "fragment_absent"), (17, 0, 99, "token_absent")],
)
def test_remplacement_par_tokens_refuse_fragment_ou_borne_absente(
    fragment_id: int, token_debut: int, token_fin: int, code: str
) -> None:
    from transcripts_pdf.service import Fragment, _resoudre_remplacements

    with pytest.raises(ErreurPreparationInvalide) as erreur:
        _resoudre_remplacements(
            [
                {
                    "categorie": "identite",
                    "fragment_id": fragment_id,
                    "token_debut": token_debut,
                    "token_fin": token_fin,
                }
            ],
            [Fragment("transcript", 17, "Élodie d'Arc")],
        )

    assert erreur.value.code == code


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
