ALTER TABLE besoins_detectes
    ADD COLUMN IF NOT EXISTS produit_id INT REFERENCES produits(id) ON DELETE CASCADE;

UPDATE besoins_detectes b
SET produit_id = t.produit_id
FROM transcripts t
WHERE b.source = 'transcript'
  AND b.transcript_id = t.id
  AND b.produit_id IS NULL;

UPDATE besoins_detectes b
SET produit_id = i.produit_id
FROM idees_featurebase i
WHERE b.source = 'idee'
  AND b.source_id = i.id
  AND b.produit_id IS NULL;

UPDATE besoins_detectes b
SET produit_id = r.produit_id
FROM retours_bizdev r
WHERE b.source = 'retour_bizdev'
  AND b.source_id = r.id
  AND b.produit_id IS NULL;

ALTER TABLE correspondances_calculees
    ADD COLUMN IF NOT EXISTS produit_id INT REFERENCES produits(id) ON DELETE CASCADE;

UPDATE correspondances_calculees c
SET produit_id = t.produit_id
FROM transcripts t
WHERE c.produit_id IS NULL
  AND EXISTS (
      SELECT 1
      FROM jsonb_array_elements(c.membres) membre
      WHERE membre->>'source' = 'transcript'
        AND (membre->>'transcript_id')::INT = t.id
  );

UPDATE correspondances_calculees c
SET produit_id = i.produit_id
FROM idees_featurebase i
WHERE c.produit_id IS NULL
  AND EXISTS (
      SELECT 1
      FROM jsonb_array_elements(c.membres) membre
      WHERE membre->>'source' = 'idee'
        AND (membre->>'source_id')::INT = i.id
  );

UPDATE correspondances_calculees c
SET produit_id = r.produit_id
FROM retours_bizdev r
WHERE c.produit_id IS NULL
  AND EXISTS (
      SELECT 1
      FROM jsonb_array_elements(c.membres) membre
      WHERE membre->>'source' = 'retour_bizdev'
        AND (membre->>'source_id')::INT = r.id
  );

CREATE INDEX IF NOT EXISTS besoins_detectes_produit_source_idx
    ON besoins_detectes (produit_id, source);

DROP INDEX IF EXISTS correspondances_calculees_produit_idx;
CREATE INDEX IF NOT EXISTS correspondances_calculees_produit_idx
    ON correspondances_calculees (produit_id);

DROP VIEW IF EXISTS features_embeddables;
CREATE VIEW features_embeddables AS
    SELECT source, source_id AS id, nom_generique AS texte, embedding,
           transcript_id, verbatim, produit_id
    FROM besoins_detectes
    WHERE statut = 'extrait' AND trim(nom_generique) <> '';
