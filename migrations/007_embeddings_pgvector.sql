CREATE EXTENSION IF NOT EXISTS vector;

ALTER TABLE fonctionnalites_transcripts ADD COLUMN embedding vector(1024);
ALTER TABLE idees_featurebase ADD COLUMN embedding vector(1024);

CREATE VIEW features_embeddables AS
    SELECT 'transcript'::text AS source, id, contenu AS texte, embedding FROM fonctionnalites_transcripts
    UNION ALL
    SELECT 'idee'::text AS source, id, titre AS texte, embedding FROM idees_featurebase;
