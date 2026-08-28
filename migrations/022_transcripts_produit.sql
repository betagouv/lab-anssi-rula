UPDATE transcripts t
SET produit_id = p.produit_id
FROM projets_recherche p
WHERE t.projet_id = p.id
  AND t.produit_id IS NULL;
