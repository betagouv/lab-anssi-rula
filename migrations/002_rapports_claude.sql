CREATE TABLE rapports_claude (
    id BIGSERIAL PRIMARY KEY,
    transcript_id INT NOT NULL REFERENCES transcripts(id) ON DELETE CASCADE,
    revision INT NOT NULL,
    empreinte TEXT NOT NULL CHECK (empreinte ~ '^[0-9a-f]{64}$'),
    cle_idempotence UUID NOT NULL UNIQUE,
    contenu_markdown TEXT NOT NULL CHECK (
        length(btrim(contenu_markdown)) > 0 AND length(contenu_markdown) <= 200000
    ),
    cree_le TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX rapports_claude_transcript_id_idx
    ON rapports_claude (transcript_id, id);
