CREATE OR REPLACE VIEW features_embeddables AS
    SELECT source,
           source_id AS id,
           nom_generique AS texte,
           embedding,
           transcript_id,
           COALESCE(verbatim, texte_original) AS verbatim
    FROM besoins_detectes
    WHERE statut = 'extrait' AND trim(nom_generique) <> '';
