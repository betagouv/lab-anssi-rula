CREATE TABLE analyses_transcripts (
    id SERIAL PRIMARY KEY,
    transcript_id INT NOT NULL UNIQUE REFERENCES transcripts(id) ON DELETE CASCADE,
    contenu TEXT NOT NULL,
    cree_le TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
