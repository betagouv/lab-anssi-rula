CREATE TABLE IF NOT EXISTS produits (
    id      SERIAL PRIMARY KEY,
    nom     TEXT NOT NULL UNIQUE,
    cree_le TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS transcripts (
    id             SERIAL PRIMARY KEY,
    titre          TEXT NOT NULL,
    contenu        TEXT NOT NULL,
    produit_id     INTEGER REFERENCES produits(id) ON DELETE SET NULL,
    date_entretien DATE,
    cree_le        TIMESTAMPTZ DEFAULT NOW(),
    modifie_le     TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS analyses (
    id          SERIAL PRIMARY KEY,
    produit_id  INTEGER REFERENCES produits(id) ON DELETE CASCADE,
    date_debut  DATE NOT NULL,
    date_fin    DATE NOT NULL,
    cree_le     TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS meta_features (
    id          SERIAL PRIMARY KEY,
    analyse_id  INTEGER REFERENCES analyses(id) ON DELETE CASCADE,
    nom         TEXT NOT NULL,
    description TEXT,
    occurrences INTEGER DEFAULT 0,
    verbatims   JSONB DEFAULT '[]'
);
