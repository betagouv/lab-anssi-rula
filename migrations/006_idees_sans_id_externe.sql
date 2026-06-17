DROP TABLE IF EXISTS idees_featurebase;

CREATE TABLE idees_featurebase (
    id SERIAL PRIMARY KEY,
    titre TEXT NOT NULL,
    nb_votes INT NOT NULL DEFAULT 0,
    importe_le TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
