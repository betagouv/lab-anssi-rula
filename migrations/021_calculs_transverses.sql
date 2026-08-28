CREATE TABLE IF NOT EXISTS calculs_transverses (
    produit_id INT PRIMARY KEY REFERENCES produits(id) ON DELETE CASCADE,
    calcule_le TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
