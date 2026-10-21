CREATE TABLE termes_liste_blanche (
    id BIGSERIAL PRIMARY KEY,
    terme TEXT NOT NULL CHECK (char_length(terme) BETWEEN 1 AND 120),
    terme_normalise TEXT NOT NULL UNIQUE,
    revision INTEGER NOT NULL DEFAULT 1 CHECK (revision > 0)
);

INSERT INTO termes_liste_blanche (terme, terme_normalise) VALUES
    ('MSS', 'mss'),
    ('Mon Service Sécurisé', 'mon service sécurisé'),
    ('LAB', 'lab'),
    ('Laboratoire d’innovation de l’ANSSI', 'laboratoire d’innovation de l’anssi'),
    ('ANSI', 'ansi'),
    ('Annecy', 'annecy')
ON CONFLICT (terme_normalise) DO NOTHING;
