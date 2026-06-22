CREATE OR REPLACE VIEW features_embeddables AS
    SELECT 'transcript'::text AS source, id, contenu AS texte, embedding, transcript_id, verbatim
    FROM fonctionnalites_transcripts
    UNION ALL
    SELECT 'idee'::text AS source, id, titre AS texte, embedding, NULL::int AS transcript_id, NULL::text AS verbatim
    FROM idees_featurebase;
