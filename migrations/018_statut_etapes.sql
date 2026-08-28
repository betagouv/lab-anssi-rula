ALTER TABLE etapes_analyses
    ADD COLUMN IF NOT EXISTS statut TEXT NOT NULL DEFAULT 'a_faire';

UPDATE etapes_analyses
SET statut = CASE
    WHEN valide IS NOT NULL THEN 'validee'
    WHEN brouillon IS NOT NULL THEN 'brouillon'
    ELSE 'a_faire'
END;
