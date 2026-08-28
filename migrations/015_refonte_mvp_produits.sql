TRUNCATE analyses, meta_features, analyses_transcripts, fonctionnalites_transcripts,
         correspondances_calculees, besoins_detectes, retours_bizdev,
         idees_featurebase, transcripts, identites, produits RESTART IDENTITY CASCADE;

CREATE TABLE projets_recherche (
    id SERIAL PRIMARY KEY,
    produit_id INT NOT NULL REFERENCES produits(id) ON DELETE CASCADE,
    nom TEXT NOT NULL,
    brief TEXT NOT NULL DEFAULT '',
    cree_le TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE scans_projets (
    projet_id INT PRIMARY KEY REFERENCES projets_recherche(id) ON DELETE CASCADE,
    brouillon TEXT NOT NULL,
    valide TEXT,
    cree_le TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    modifie_le TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE transcripts ADD COLUMN projet_id INT REFERENCES projets_recherche(id) ON DELETE CASCADE;
ALTER TABLE transcripts ADD COLUMN participant TEXT;
ALTER TABLE transcripts ADD COLUMN moderateur TEXT;
ALTER TABLE transcripts ADD COLUMN note_moderateur TEXT NOT NULL DEFAULT '';

ALTER TABLE retours_bizdev ADD COLUMN produit_id INT NOT NULL REFERENCES produits(id) ON DELETE CASCADE;
ALTER TABLE idees_featurebase ADD COLUMN produit_id INT NOT NULL REFERENCES produits(id) ON DELETE CASCADE;
