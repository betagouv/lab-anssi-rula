DROP VIEW IF EXISTS features_embeddables CASCADE;
DROP TABLE IF EXISTS calculs_transverses, etapes_analyses, prompts_projets,
    prompts_produits, scans_projets, jobs_analyse_transcripts,
    analyses_transcripts_pdf, analyses_transcripts,
    fonctionnalites_transcripts, besoins_detectes,
    correspondances_calculees, retours_bizdev, idees_featurebase,
    meta_features, analyses, projets_recherche, identites CASCADE;

DROP TRIGGER IF EXISTS transcripts_invalidation_insert_delete ON transcripts;
DROP TRIGGER IF EXISTS transcripts_invalidation_update ON transcripts;
DROP FUNCTION IF EXISTS invalider_source_transcript();
DROP FUNCTION IF EXISTS invalider_configuration_projet();
DROP FUNCTION IF EXISTS invalider_suppression_projet();
DROP FUNCTION IF EXISTS invalider_projet(INT);

DELETE FROM transcripts
WHERE NOT confirme
   OR type_source NOT IN ('produit', 'bizdev')
   OR produit_id IS NULL
   OR produit_id NOT IN (SELECT id FROM produits WHERE nom IN ('MSS', 'MSC'));

DELETE FROM produits WHERE nom NOT IN ('MSS', 'MSC');

ALTER TABLE transcripts
    DROP COLUMN IF EXISTS titre,
    DROP COLUMN IF EXISTS identite_id,
    DROP COLUMN IF EXISTS projet_id,
    DROP COLUMN IF EXISTS participant,
    DROP COLUMN IF EXISTS moderateur,
    DROP COLUMN IF EXISTS note_moderateur,
    DROP COLUMN IF EXISTS revision_corpus;

ALTER TABLE transcripts
    DROP CONSTRAINT IF EXISTS transcripts_type_source_check,
    DROP CONSTRAINT IF EXISTS transcripts_check,
    DROP CONSTRAINT IF EXISTS transcripts_confirme_check,
    DROP CONSTRAINT IF EXISTS transcripts_projet_id_produit_id_fkey,
    ALTER COLUMN type_source SET DEFAULT 'produit';

ALTER TABLE transcripts
    ADD CONSTRAINT transcripts_type_source_check
        CHECK (type_source IN ('produit', 'bizdev')),
    ADD CONSTRAINT transcripts_confirme_check CHECK (confirme);

CREATE INDEX IF NOT EXISTS transcripts_produit_type_idx
    ON transcripts(produit_id, type_source);
