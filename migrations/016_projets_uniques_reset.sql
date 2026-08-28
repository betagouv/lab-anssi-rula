TRUNCATE analyses, meta_features, analyses_transcripts, fonctionnalites_transcripts,
         correspondances_calculees, besoins_detectes, retours_bizdev,
         idees_featurebase, scans_projets, projets_recherche, transcripts,
         identites, produits RESTART IDENTITY CASCADE;

CREATE UNIQUE INDEX projets_recherche_produit_nom_unique
    ON projets_recherche (produit_id, lower(btrim(nom)));

INSERT INTO produits (nom) VALUES ('MQC'), ('MSC'), ('MSS');
