CREATE TABLE termes_liste_noire (
    id BIGSERIAL PRIMARY KEY,
    terme TEXT NOT NULL CHECK (char_length(terme) BETWEEN 1 AND 120),
    terme_normalise TEXT NOT NULL UNIQUE,
    revision INTEGER NOT NULL DEFAULT 1 CHECK (revision > 0)
);

ALTER TABLE transcripts
    ADD COLUMN termes_imposes JSONB NOT NULL DEFAULT '[]'::jsonb;
