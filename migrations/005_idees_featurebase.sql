CREATE TABLE idees_featurebase (
    id SERIAL PRIMARY KEY,
    id_externe TEXT NOT NULL UNIQUE,
    titre TEXT NOT NULL,
    nb_votes INT NOT NULL DEFAULT 0,
    sync_le TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
