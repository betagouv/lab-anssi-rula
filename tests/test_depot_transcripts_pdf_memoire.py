from datetime import date

from infra.memoire.depot_transcripts_pdf import DepotTranscriptsPdfMemoire


def test_depot_memoire_gere_le_cycle_de_vie_des_transcripts() -> None:
    depot = DepotTranscriptsPdfMemoire()
    locuteurs = [{"identifiant": "SPEAKER_01", "role": "externe"}]
    source = depot.ajouter(
        "bizdev", 2, "reunion.pdf", date(2026, 10, 21), "texte", "contexte", locuteurs
    )
    assert depot.obtenir(source.id) == source
    assert depot.lister(2) == [source]
    modifie = depot.modifier(source.id, date(2026, 10, 20), "texte modifie", "", [])
    assert modifie is not None
    assert depot.obtenir(source.id) == modifie
    assert depot.supprimer(source.id)
    assert depot.obtenir(source.id) is None
    assert not depot.supprimer(source.id)
