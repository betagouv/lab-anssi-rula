CREATE TABLE correspondances_calculees (
    id SERIAL PRIMARY KEY,
    libelle TEXT NOT NULL,
    occurrences INT NOT NULL,
    membres JSONB NOT NULL,
    calcule_le TIMESTAMPTZ DEFAULT NOW()
);
