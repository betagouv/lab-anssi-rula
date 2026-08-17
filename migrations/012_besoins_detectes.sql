CREATE TABLE besoins_detectes (
    id SERIAL PRIMARY KEY,
    source TEXT NOT NULL CHECK (source IN ('transcript', 'idee', 'retour_bizdev')),
    source_id INT NOT NULL,
    texte_original TEXT NOT NULL,
    nom_generique TEXT NOT NULL,
    verbatim TEXT,
    transcript_id INT REFERENCES transcripts(id) ON DELETE CASCADE,
    statut TEXT NOT NULL DEFAULT 'extrait',
    embedding vector(1024),
    cree_le TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (source, source_id)
);

CREATE INDEX besoins_detectes_source_idx ON besoins_detectes(source);

INSERT INTO besoins_detectes (source, source_id, texte_original, nom_generique, verbatim, transcript_id)
SELECT 'transcript', id, contenu, contenu, verbatim, transcript_id
FROM fonctionnalites_transcripts
ON CONFLICT (source, source_id) DO NOTHING;

INSERT INTO besoins_detectes (source, source_id, texte_original, nom_generique)
SELECT 'idee', id, titre, titre
FROM idees_featurebase
ON CONFLICT (source, source_id) DO NOTHING;

INSERT INTO besoins_detectes (source, source_id, texte_original, nom_generique, verbatim)
SELECT 'retour_bizdev', id, verbatim, verbatim, verbatim
FROM retours_bizdev
ON CONFLICT (source, source_id) DO NOTHING;

CREATE OR REPLACE VIEW features_embeddables AS
    SELECT source, source_id AS id, nom_generique AS texte, embedding, transcript_id, verbatim
    FROM besoins_detectes
    WHERE statut = 'extrait' AND trim(nom_generique) <> '';
