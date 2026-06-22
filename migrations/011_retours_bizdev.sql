CREATE TABLE retours_bizdev (
    id SERIAL PRIMARY KEY,
    verbatim TEXT NOT NULL,
    categorie TEXT,
    item TEXT,
    role TEXT,
    qui TEXT,
    date_retour TEXT,
    importe_le TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    embedding vector(1024)
);

CREATE OR REPLACE VIEW features_embeddables AS
    SELECT 'transcript'::text AS source, id, contenu AS texte, embedding, transcript_id, verbatim
    FROM fonctionnalites_transcripts
    UNION ALL
    SELECT 'idee'::text, id, titre, embedding, NULL::int, NULL::text
    FROM idees_featurebase
    UNION ALL
    SELECT 'retour_bizdev'::text, id, verbatim, embedding, NULL::int,
           NULLIF(trim(coalesce(categorie, '') || ' — ' || coalesce(item, '')), ' — ')
    FROM retours_bizdev;
