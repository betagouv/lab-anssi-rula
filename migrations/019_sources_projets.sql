ALTER TABLE retours_bizdev
    ADD COLUMN IF NOT EXISTS projet_id INT REFERENCES projets_recherche(id) ON DELETE CASCADE;

ALTER TABLE idees_featurebase
    ADD COLUMN IF NOT EXISTS projet_id INT REFERENCES projets_recherche(id) ON DELETE CASCADE;

CREATE INDEX IF NOT EXISTS retours_bizdev_produit_projet_idx
    ON retours_bizdev (produit_id, projet_id);

CREATE INDEX IF NOT EXISTS idees_featurebase_produit_projet_idx
    ON idees_featurebase (produit_id, projet_id);
