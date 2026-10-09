CREATE TABLE IF NOT EXISTS produits (
    id      SERIAL PRIMARY KEY,
    nom     TEXT NOT NULL UNIQUE,
    cree_le TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS transcripts (
    id             SERIAL PRIMARY KEY,
    titre          TEXT NOT NULL,
    contenu        TEXT NOT NULL,
    produit_id     INTEGER REFERENCES produits(id) ON DELETE SET NULL,
    date_entretien DATE,
    cree_le        TIMESTAMPTZ DEFAULT NOW(),
    modifie_le     TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS analyses (
    id          SERIAL PRIMARY KEY,
    produit_id  INTEGER REFERENCES produits(id) ON DELETE CASCADE,
    date_debut  DATE NOT NULL,
    date_fin    DATE NOT NULL,
    cree_le     TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS meta_features (
    id          SERIAL PRIMARY KEY,
    analyse_id  INTEGER REFERENCES analyses(id) ON DELETE CASCADE,
    nom         TEXT NOT NULL,
    description TEXT,
    occurrences INTEGER DEFAULT 0,
    verbatims   JSONB DEFAULT '[]'
);


CREATE TABLE IF NOT EXISTS identites (
    id      SERIAL PRIMARY KEY,
    nom     TEXT NOT NULL UNIQUE,
    cree_le TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE transcripts
    ADD COLUMN IF NOT EXISTS identite_id INTEGER REFERENCES identites(id) ON DELETE SET NULL;

ALTER TABLE transcripts
    ALTER COLUMN titre DROP NOT NULL;


CREATE TABLE analyses_transcripts (
    id SERIAL PRIMARY KEY,
    transcript_id INT NOT NULL UNIQUE REFERENCES transcripts(id) ON DELETE CASCADE,
    contenu TEXT NOT NULL,
    cree_le TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


CREATE TABLE fonctionnalites_transcripts (
    id SERIAL PRIMARY KEY,
    transcript_id INT NOT NULL REFERENCES transcripts(id) ON DELETE CASCADE,
    contenu TEXT NOT NULL,
    cree_le TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


CREATE TABLE idees_featurebase (
    id SERIAL PRIMARY KEY,
    id_externe TEXT NOT NULL UNIQUE,
    titre TEXT NOT NULL,
    nb_votes INT NOT NULL DEFAULT 0,
    sync_le TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


DROP TABLE IF EXISTS idees_featurebase;

CREATE TABLE idees_featurebase (
    id SERIAL PRIMARY KEY,
    titre TEXT NOT NULL,
    nb_votes INT NOT NULL DEFAULT 0,
    importe_le TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


CREATE EXTENSION IF NOT EXISTS vector;

ALTER TABLE fonctionnalites_transcripts ADD COLUMN embedding vector(1024);
ALTER TABLE idees_featurebase ADD COLUMN embedding vector(1024);

CREATE VIEW features_embeddables AS
    SELECT 'transcript'::text AS source, id, contenu AS texte, embedding FROM fonctionnalites_transcripts
    UNION ALL
    SELECT 'idee'::text AS source, id, titre AS texte, embedding FROM idees_featurebase;


ALTER TABLE fonctionnalites_transcripts ADD COLUMN verbatim TEXT;


CREATE OR REPLACE VIEW features_embeddables AS
    SELECT 'transcript'::text AS source, id, contenu AS texte, embedding, transcript_id, verbatim
    FROM fonctionnalites_transcripts
    UNION ALL
    SELECT 'idee'::text AS source, id, titre AS texte, embedding, NULL::int AS transcript_id, NULL::text AS verbatim
    FROM idees_featurebase;


CREATE TABLE correspondances_calculees (
    id SERIAL PRIMARY KEY,
    libelle TEXT NOT NULL,
    occurrences INT NOT NULL,
    membres JSONB NOT NULL,
    calcule_le TIMESTAMPTZ DEFAULT NOW()
);


CREATE TABLE retours_bizdev (
    id SERIAL PRIMARY KEY,
    verbatim TEXT NOT NULL,
    categorie TEXT,
    item TEXT,
    role TEXT,
    qui TEXT,
    date_retour TEXT,
    importe_le TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    embedding vector(1024)
);

CREATE OR REPLACE VIEW features_embeddables AS
    SELECT 'transcript'::text AS source, id, contenu AS texte, embedding, transcript_id, verbatim
    FROM fonctionnalites_transcripts
    UNION ALL
    SELECT 'idee'::text, id, titre, embedding, NULL::int, NULL::text
    FROM idees_featurebase
    UNION ALL
    SELECT 'retour_bizdev'::text, id, verbatim, embedding, NULL::int,
           NULLIF(trim(coalesce(categorie, '') || ' — ' || coalesce(item, '')), ' — ')
    FROM retours_bizdev;


CREATE TABLE besoins_detectes (
    id SERIAL PRIMARY KEY,
    source TEXT NOT NULL CHECK (source IN ('transcript', 'idee', 'retour_bizdev')),
    source_id INT NOT NULL,
    texte_original TEXT NOT NULL,
    nom_generique TEXT NOT NULL,
    verbatim TEXT,
    transcript_id INT REFERENCES transcripts(id) ON DELETE CASCADE,
    statut TEXT NOT NULL DEFAULT 'extrait',
    embedding vector(1024),
    cree_le TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (source, source_id)
);

CREATE INDEX besoins_detectes_source_idx ON besoins_detectes(source);

INSERT INTO besoins_detectes (source, source_id, texte_original, nom_generique, verbatim, transcript_id)
SELECT 'transcript', id, contenu, contenu, verbatim, transcript_id
FROM fonctionnalites_transcripts
ON CONFLICT (source, source_id) DO NOTHING;

INSERT INTO besoins_detectes (source, source_id, texte_original, nom_generique)
SELECT 'idee', id, titre, titre
FROM idees_featurebase
ON CONFLICT (source, source_id) DO NOTHING;

INSERT INTO besoins_detectes (source, source_id, texte_original, nom_generique, verbatim)
SELECT 'retour_bizdev', id, verbatim, verbatim, verbatim
FROM retours_bizdev
ON CONFLICT (source, source_id) DO NOTHING;

CREATE OR REPLACE VIEW features_embeddables AS
    SELECT source, source_id AS id, nom_generique AS texte, embedding, transcript_id, verbatim
    FROM besoins_detectes
    WHERE statut = 'extrait' AND trim(nom_generique) <> '';


-- Certains exports historiques contiennent des caractères de contrôle à la
-- place des apostrophes et guillemets. Ils sont illisibles dans l'IHM.
UPDATE idees_featurebase
SET titre = replace(replace(replace(titre, chr(25), '’'), chr(28), '«'), chr(29), '»');

UPDATE retours_bizdev
SET verbatim = replace(replace(replace(verbatim, chr(25), '’'), chr(28), '«'), chr(29), '»'),
    categorie = replace(replace(replace(categorie, chr(25), '’'), chr(28), '«'), chr(29), '»'),
    item = replace(replace(replace(item, chr(25), '’'), chr(28), '«'), chr(29), '»'),
    role = replace(replace(replace(role, chr(25), '’'), chr(28), '«'), chr(29), '»'),
    qui = replace(replace(replace(qui, chr(25), '’'), chr(28), '«'), chr(29), '»');

UPDATE besoins_detectes
SET texte_original = replace(replace(replace(texte_original, chr(25), '’'), chr(28), '«'), chr(29), '»'),
    nom_generique = replace(replace(replace(nom_generique, chr(25), '’'), chr(28), '«'), chr(29), '»'),
    verbatim = replace(replace(replace(verbatim, chr(25), '’'), chr(28), '«'), chr(29), '»');


CREATE OR REPLACE VIEW features_embeddables AS
    SELECT source,
           source_id AS id,
           nom_generique AS texte,
           embedding,
           transcript_id,
           COALESCE(verbatim, texte_original) AS verbatim
    FROM besoins_detectes
    WHERE statut = 'extrait' AND trim(nom_generique) <> '';


TRUNCATE analyses, meta_features, analyses_transcripts, fonctionnalites_transcripts,
         correspondances_calculees, besoins_detectes, retours_bizdev,
         idees_featurebase, transcripts, identites, produits RESTART IDENTITY CASCADE;

CREATE TABLE projets_recherche (
    id SERIAL PRIMARY KEY,
    produit_id INT NOT NULL REFERENCES produits(id) ON DELETE CASCADE,
    nom TEXT NOT NULL,
    brief TEXT NOT NULL DEFAULT '',
    cree_le TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE scans_projets (
    projet_id INT PRIMARY KEY REFERENCES projets_recherche(id) ON DELETE CASCADE,
    brouillon TEXT NOT NULL,
    valide TEXT,
    cree_le TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    modifie_le TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE transcripts ADD COLUMN projet_id INT REFERENCES projets_recherche(id) ON DELETE CASCADE;
ALTER TABLE transcripts ADD COLUMN participant TEXT;
ALTER TABLE transcripts ADD COLUMN moderateur TEXT;
ALTER TABLE transcripts ADD COLUMN note_moderateur TEXT NOT NULL DEFAULT '';

ALTER TABLE retours_bizdev ADD COLUMN produit_id INT NOT NULL REFERENCES produits(id) ON DELETE CASCADE;
ALTER TABLE idees_featurebase ADD COLUMN produit_id INT NOT NULL REFERENCES produits(id) ON DELETE CASCADE;


TRUNCATE analyses, meta_features, analyses_transcripts, fonctionnalites_transcripts,
         correspondances_calculees, besoins_detectes, retours_bizdev,
         idees_featurebase, scans_projets, projets_recherche, transcripts,
         identites, produits RESTART IDENTITY CASCADE;

CREATE UNIQUE INDEX projets_recherche_produit_nom_unique
    ON projets_recherche (produit_id, lower(btrim(nom)));

INSERT INTO produits (nom) VALUES ('MQC'), ('MSC'), ('MSS');


CREATE TABLE prompts_produits (
    produit_id INT NOT NULL REFERENCES produits(id) ON DELETE CASCADE,
    cle TEXT NOT NULL,
    libelle TEXT NOT NULL,
    contenu TEXT NOT NULL DEFAULT '',
    ordre SMALLINT NOT NULL,
    PRIMARY KEY (produit_id, cle)
);

CREATE TABLE prompts_projets (
    projet_id INT NOT NULL REFERENCES projets_recherche(id) ON DELETE CASCADE,
    cle TEXT NOT NULL,
    libelle TEXT NOT NULL,
    contenu TEXT NOT NULL DEFAULT '',
    ordre SMALLINT NOT NULL,
    PRIMARY KEY (projet_id, cle)
);

CREATE TABLE etapes_analyses (
    projet_id INT NOT NULL REFERENCES projets_recherche(id) ON DELETE CASCADE,
    cle TEXT NOT NULL,
    libelle TEXT NOT NULL,
    ordre SMALLINT NOT NULL,
    prompt TEXT NOT NULL DEFAULT '',
    brouillon TEXT,
    valide TEXT,
    statut TEXT NOT NULL DEFAULT 'a_faire',
    cree_le TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    modifie_le TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (projet_id, cle)
);

INSERT INTO prompts_produits (produit_id, cle, libelle, contenu, ordre)
SELECT produits.id, valeurs.cle, valeurs.libelle, valeurs.contenu, valeurs.ordre
FROM produits
CROSS JOIN (VALUES
    ('role', 'Le rôle', 'Tu es un·e product researcher senior spécialisé·e dans l’analyse d’entretiens utilisateurs B2B.', 1),
    ('contexte_produit', 'Contexte produit', '', 2),
    ('contexte_brief', 'Contexte du brief', '', 3),
    ('contexte_projet', 'Contexte du projet', '', 4),
    ('regles', 'Les règles', 'Ne rien inventer. Distinguer les faits, les interprétations et les signaux faibles. Signaler les biais, les données manquantes et le nombre de transcripts analysés. Vérifier chaque verbatim dans les transcripts sources.', 5),
    ('instructions_sortie', 'Instructions de sortie', 'Répondre en français et en Markdown structuré. Citer les verbatims utiles et rester honnête lorsque la matière est insuffisante.', 6),
    ('consigne_scan-neutre', 'Consigne — Scan neutre', 'Scanne chaque transcript individuellement, sans interprétation ni généralisation. Extrais les verbatims exacts, les pratiques, frictions, alternatives, émotions et signaux à noter.', 7),
    ('consigne_points-a-retenir', 'Consigne — Points à retenir', 'À partir du scan neutre validé, regroupe les faits récurrents et les signaux faibles. Indique la fréquence et le niveau de confiance sans masquer les contradictions.', 8),
    ('consigne_thematisation', 'Consigne — Thématisation', 'Organise les points à retenir en thèmes explicites et exploitables. Chaque thème doit rester relié aux verbatims et aux transcripts sources.', 9)
) AS valeurs(cle, libelle, contenu, ordre);

UPDATE prompts_produits
SET contenu = 'MSS est utilisé par des RSSI, DPO et chefs de projet sécurité dans des collectivités, établissements publics, ministères et préfectures. Le produit permet d’enregistrer un service numérique, suivre les mesures de sécurité, mener une homologation et gérer les contributeurs. La recherche porte sur la gestion des organisations : services rattachés, délégations, hiérarchies et arrivées ou départs.'
WHERE cle = 'contexte_produit'
  AND produit_id = (SELECT id FROM produits WHERE nom = 'MSS');

UPDATE prompts_produits
SET contenu = $$MSS est utilisé par des RSSI, DPO et chefs de projet sécurité dans des collectivités territoriales, établissements publics, ministères et préfectures.

Le produit permet d’enregistrer un service numérique, suivre les mesures de sécurité à appliquer, mener une homologation (analyse de risque, plan d’action et décision) et gérer les contributeurs.

La recherche porte sur la fonctionnalité « Gestion des organisations » : voir et piloter les services rattachés à une organisation, déléguer des responsabilités, structurer une hiérarchie nationale/régionale/unité et gérer les arrivées et départs. L’authentification se fait via ProConnect avec rattachement à un SIRET.

Dimensions à extraire :
1. Profil de la personne interviewée : fonction, organisation, contexte et niveau de maturité.
2. Compréhension du sujet : définition de la gestion des organisations avec les mots de la personne.
3. Besoins explicites : fonctionnalités demandées et problèmes à résoudre.
4. Besoins implicites : frustrations, contraintes et attentes non dites.
5. Points de douleur actuels : pertes de temps, risques et dysfonctionnements.
6. Contournements et outils utilisés : Excel, outils tiers et procédures manuelles.
7. Cas concrets cités : situations vécues et exemples précis.
8. Priorisation : priorités exprimées ou déductibles de l’entretien.
9. Questions ouvertes et contradictions : sujets à retester ou à approfondir.
10. Vocabulaire et concepts métier : termes spécifiques et définitions données.$$
WHERE cle = 'contexte_produit'
  AND produit_id = (SELECT id FROM produits WHERE nom = 'MSS');

UPDATE prompts_produits
SET contenu = $$Ne rien inventer. N’extrais que ce qui est explicitement dit ou clairement implicite.

Cite un verbatim direct pour chaque besoin ou douleur et distingue fait et interprétation.

N’utilise pas de jargon de consultant et signale les passages incompréhensibles ou les transcripts de mauvaise qualité.

Respecte l’anonymisation et conserve les prénoms cités lorsqu’ils sont nécessaires au sens.

Pour chaque apprentissage, indique la fréquence et le niveau de confiance. Distingue les tendances confirmées des signaux faibles, signale les biais et les données manquantes, confirme le nombre de transcripts analysés et ne cite que des verbatims présents dans les sources.$$
WHERE cle = 'regles'
  AND produit_id = (SELECT id FROM produits WHERE nom = 'MSS');

UPDATE prompts_produits
SET contenu = $$Retourne un Markdown structuré en français avec exactement les sections suivantes :

## 1. Profil
## 2. Compréhension du sujet
## 3. Besoins identifiés
## 4. Points de douleur
## 5. Cas concrets cités
## 6. Contournements actuels
## 7. Priorisation (si exprimée)
## 8. Questions ouvertes / à retester
## 9. Vocabulaire métier remarqué
## 10. Synthèse en 3 phrases

Ne produis pas de tableau récapitulatif artificiel si la matière est mince.$$
WHERE cle = 'instructions_sortie'
  AND produit_id = (SELECT id FROM produits WHERE nom = 'MSS');


ALTER TABLE etapes_analyses
    ADD COLUMN IF NOT EXISTS statut TEXT NOT NULL DEFAULT 'a_faire';

UPDATE etapes_analyses
SET statut = CASE
    WHEN valide IS NOT NULL THEN 'validee'
    WHEN brouillon IS NOT NULL THEN 'brouillon'
    ELSE 'a_faire'
END;


ALTER TABLE retours_bizdev
    ADD COLUMN IF NOT EXISTS projet_id INT REFERENCES projets_recherche(id) ON DELETE CASCADE;

ALTER TABLE idees_featurebase
    ADD COLUMN IF NOT EXISTS projet_id INT REFERENCES projets_recherche(id) ON DELETE CASCADE;

CREATE INDEX IF NOT EXISTS retours_bizdev_produit_projet_idx
    ON retours_bizdev (produit_id, projet_id);

CREATE INDEX IF NOT EXISTS idees_featurebase_produit_projet_idx
    ON idees_featurebase (produit_id, projet_id);


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


CREATE TABLE IF NOT EXISTS calculs_transverses (
    produit_id INT PRIMARY KEY REFERENCES produits(id) ON DELETE CASCADE,
    calcule_le TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


UPDATE transcripts t
SET produit_id = p.produit_id
FROM projets_recherche p
WHERE t.projet_id = p.id
  AND t.produit_id IS NULL;
