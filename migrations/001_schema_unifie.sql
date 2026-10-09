CREATE EXTENSION IF NOT EXISTS vector;

DROP VIEW IF EXISTS features_embeddables;
DROP TABLE IF EXISTS calculs_transverses, etapes_analyses, prompts_projets,
    prompts_produits, scans_projets, jobs_analyse_transcripts,
    analyses_transcripts_pdf, analyses_transcripts,
    fonctionnalites_transcripts, besoins_detectes,
    correspondances_calculees, retours_bizdev, idees_featurebase,
    meta_features, analyses, transcripts, projets_recherche, identites,
    produits;

CREATE TABLE produits (
    id SERIAL PRIMARY KEY,
    nom TEXT NOT NULL UNIQUE,
    cree_le TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE identites (
    id SERIAL PRIMARY KEY,
    nom TEXT NOT NULL UNIQUE,
    cree_le TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE projets_recherche (
    id SERIAL PRIMARY KEY,
    produit_id INT NOT NULL REFERENCES produits(id) ON DELETE CASCADE,
    nom TEXT NOT NULL,
    brief TEXT NOT NULL DEFAULT '',
    revision_corpus INT NOT NULL DEFAULT 1,
    cree_le TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (id, produit_id)
);

CREATE UNIQUE INDEX projets_recherche_produit_nom_unique
    ON projets_recherche (produit_id, lower(btrim(nom)));

CREATE TABLE transcripts (
    id SERIAL PRIMARY KEY,
    titre TEXT,
    contenu TEXT NOT NULL,
    identite_id INT REFERENCES identites(id) ON DELETE SET NULL,
    produit_id INT REFERENCES produits(id) ON DELETE CASCADE,
    projet_id INT,
    participant TEXT,
    moderateur TEXT,
    note_moderateur TEXT NOT NULL DEFAULT '',
    date_entretien DATE,
    type_source TEXT NOT NULL DEFAULT 'ux'
        CHECK (type_source IN ('ux', 'produit', 'bizdev')),
    contexte TEXT NOT NULL DEFAULT '',
    locuteurs JSONB NOT NULL DEFAULT '[]',
    nom_fichier TEXT NOT NULL DEFAULT 'transcript',
    revision_corpus INT NOT NULL DEFAULT 1,
    confirme BOOLEAN NOT NULL DEFAULT TRUE,
    cree_le TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    modifie_le TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    FOREIGN KEY (projet_id, produit_id)
        REFERENCES projets_recherche(id, produit_id) ON DELETE CASCADE,
    CHECK (
        (type_source = 'ux')
        OR (type_source = 'produit' AND projet_id IS NOT NULL AND produit_id IS NOT NULL)
        OR (type_source = 'bizdev' AND projet_id IS NULL AND produit_id IS NOT NULL)
    )
);

CREATE INDEX transcripts_projet_type_idx ON transcripts(projet_id, type_source);
CREATE INDEX transcripts_produit_type_idx ON transcripts(produit_id, type_source);

CREATE TABLE analyses (
    id SERIAL PRIMARY KEY,
    produit_id INT REFERENCES produits(id) ON DELETE CASCADE,
    date_debut DATE NOT NULL,
    date_fin DATE NOT NULL,
    cree_le TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE meta_features (
    id SERIAL PRIMARY KEY,
    analyse_id INT REFERENCES analyses(id) ON DELETE CASCADE,
    nom TEXT NOT NULL,
    description TEXT,
    occurrences INT NOT NULL DEFAULT 0,
    verbatims JSONB NOT NULL DEFAULT '[]'
);

CREATE TABLE analyses_transcripts (
    id SERIAL PRIMARY KEY,
    transcript_id INT NOT NULL UNIQUE REFERENCES transcripts(id) ON DELETE CASCADE,
    contenu TEXT NOT NULL,
    cree_le TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    revision INT NOT NULL DEFAULT 1,
    schema_version TEXT NOT NULL DEFAULT 'ux-v1',
    prompt_version TEXT NOT NULL DEFAULT 'ux-v1'
);

CREATE TABLE analyses_transcripts_pdf (
    id SERIAL PRIMARY KEY,
    transcript_id INT NOT NULL REFERENCES transcripts(id) ON DELETE CASCADE,
    revision INT NOT NULL,
    type_source TEXT NOT NULL CHECK (type_source IN ('produit', 'bizdev')),
    contenu JSONB NOT NULL,
    schema_version TEXT NOT NULL,
    prompt_version TEXT NOT NULL,
    cree_le TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (transcript_id, revision)
);

CREATE TABLE fonctionnalites_transcripts (
    id SERIAL PRIMARY KEY,
    transcript_id INT NOT NULL REFERENCES transcripts(id) ON DELETE CASCADE,
    contenu TEXT NOT NULL,
    verbatim TEXT,
    cree_le TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE idees_featurebase (
    id SERIAL PRIMARY KEY,
    titre TEXT NOT NULL,
    nb_votes INT NOT NULL DEFAULT 0,
    importe_le TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    embedding vector(1024),
    produit_id INT NOT NULL REFERENCES produits(id) ON DELETE CASCADE,
    projet_id INT,
    FOREIGN KEY (projet_id, produit_id)
        REFERENCES projets_recherche(id, produit_id) ON DELETE CASCADE
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
    embedding vector(1024),
    produit_id INT NOT NULL REFERENCES produits(id) ON DELETE CASCADE,
    projet_id INT,
    FOREIGN KEY (projet_id, produit_id)
        REFERENCES projets_recherche(id, produit_id) ON DELETE CASCADE
);

CREATE INDEX retours_bizdev_produit_projet_idx ON retours_bizdev(produit_id, projet_id);
CREATE INDEX idees_featurebase_produit_projet_idx ON idees_featurebase(produit_id, projet_id);

CREATE TABLE besoins_detectes (
    id SERIAL PRIMARY KEY,
    source TEXT NOT NULL CHECK (source IN (
        'transcript', 'transcript_produit', 'transcript_bizdev', 'idee', 'retour_bizdev'
    )),
    source_id INT NOT NULL,
    texte_original TEXT NOT NULL,
    nom_generique TEXT NOT NULL,
    verbatim TEXT,
    transcript_id INT REFERENCES transcripts(id) ON DELETE CASCADE,
    statut TEXT NOT NULL DEFAULT 'extrait',
    embedding vector(1024),
    cree_le TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    produit_id INT REFERENCES produits(id) ON DELETE CASCADE,
    UNIQUE (source, source_id)
);

CREATE INDEX besoins_detectes_source_idx ON besoins_detectes(source);
CREATE INDEX besoins_detectes_produit_source_idx ON besoins_detectes(produit_id, source);

CREATE TABLE correspondances_calculees (
    id SERIAL PRIMARY KEY,
    libelle TEXT NOT NULL,
    occurrences INT NOT NULL,
    membres JSONB NOT NULL,
    calcule_le TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    produit_id INT REFERENCES produits(id) ON DELETE CASCADE
);

CREATE INDEX correspondances_calculees_produit_idx
    ON correspondances_calculees(produit_id);

CREATE TABLE scans_projets (
    projet_id INT PRIMARY KEY REFERENCES projets_recherche(id) ON DELETE CASCADE,
    revision INT NOT NULL DEFAULT 1,
    brouillon TEXT NOT NULL,
    valide TEXT,
    cree_le TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    modifie_le TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

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
    revision INT NOT NULL DEFAULT 1,
    cree_le TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    modifie_le TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (projet_id, cle)
);

CREATE TABLE calculs_transverses (
    produit_id INT PRIMARY KEY REFERENCES produits(id) ON DELETE CASCADE,
    calcule_le TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE jobs_analyse_transcripts (
    id BIGSERIAL PRIMARY KEY,
    transcript_id INT NOT NULL REFERENCES transcripts(id) ON DELETE CASCADE,
    revision INT NOT NULL,
    revision_projet INT,
    statut TEXT NOT NULL DEFAULT 'attente'
        CHECK (statut IN ('attente', 'en_cours', 'termine', 'echec')),
    jeton UUID,
    bail_jusqua TIMESTAMPTZ,
    tentatives INT NOT NULL DEFAULT 0,
    erreur TEXT,
    cree_le TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    modifie_le TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (transcript_id, revision)
);

CREATE INDEX jobs_analyse_reprise_idx
    ON jobs_analyse_transcripts(statut, bail_jusqua);

CREATE FUNCTION invalider_projet(projet INT) RETURNS VOID AS $$
BEGIN
    UPDATE projets_recherche
    SET revision_corpus = revision_corpus + 1
    WHERE id = projet;
    DELETE FROM scans_projets WHERE projet_id = projet;
    UPDATE etapes_analyses
    SET brouillon = NULL, valide = NULL, statut = 'a_faire',
        revision = revision + 1, modifie_le = NOW()
    WHERE projet_id = projet;
    UPDATE jobs_analyse_transcripts
    SET statut = 'echec', jeton = NULL, bail_jusqua = NULL,
        erreur = 'Le corpus a changé.', modifie_le = NOW()
    WHERE transcript_id IN (SELECT id FROM transcripts WHERE projet_id = projet)
      AND statut IN ('attente', 'en_cours');
    DELETE FROM correspondances_calculees
    WHERE produit_id = (SELECT produit_id FROM projets_recherche WHERE id = projet);
    DELETE FROM calculs_transverses
    WHERE produit_id = (SELECT produit_id FROM projets_recherche WHERE id = projet);
END;
$$ LANGUAGE plpgsql;

CREATE FUNCTION invalider_source_transcript() RETURNS TRIGGER AS $$
DECLARE
    projet_avant INT;
    projet_apres INT;
    produit_avant INT;
    produit_apres INT;
BEGIN
    IF TG_OP <> 'INSERT' THEN
        projet_avant := OLD.projet_id;
        produit_avant := OLD.produit_id;
    END IF;
    IF TG_OP <> 'DELETE' THEN
        projet_apres := NEW.projet_id;
        produit_apres := NEW.produit_id;
    END IF;
    IF TG_OP = 'UPDATE' THEN
        DELETE FROM analyses_transcripts WHERE transcript_id = NEW.id;
        DELETE FROM analyses_transcripts_pdf WHERE transcript_id = NEW.id;
        DELETE FROM fonctionnalites_transcripts WHERE transcript_id = NEW.id;
        DELETE FROM besoins_detectes WHERE transcript_id = NEW.id;
        DELETE FROM jobs_analyse_transcripts WHERE transcript_id = NEW.id;
    END IF;
    IF projet_avant IS NOT NULL THEN
        PERFORM invalider_projet(projet_avant);
    END IF;
    IF projet_apres IS NOT NULL AND projet_apres IS DISTINCT FROM projet_avant THEN
        PERFORM invalider_projet(projet_apres);
    ELSIF projet_apres IS NULL AND projet_avant IS NULL THEN
        DELETE FROM correspondances_calculees
        WHERE produit_id = COALESCE(produit_apres, produit_avant);
        DELETE FROM calculs_transverses
        WHERE produit_id = COALESCE(produit_apres, produit_avant);
        UPDATE jobs_analyse_transcripts
        SET statut = 'echec', jeton = NULL, bail_jusqua = NULL,
            erreur = 'Le corpus a changé.', modifie_le = NOW()
        WHERE transcript_id = COALESCE(NEW.id, OLD.id)
          AND statut IN ('attente', 'en_cours');
    END IF;
    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER transcripts_invalidation_insert_delete
AFTER INSERT OR DELETE ON transcripts
FOR EACH ROW EXECUTE FUNCTION invalider_source_transcript();

CREATE TRIGGER transcripts_invalidation_update
AFTER UPDATE OF contenu, contexte, locuteurs, date_entretien, projet_id, produit_id
ON transcripts FOR EACH ROW EXECUTE FUNCTION invalider_source_transcript();

CREATE FUNCTION invalider_configuration_projet() RETURNS TRIGGER AS $$
BEGIN
    PERFORM invalider_projet(NEW.id);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER projets_invalidation_update
AFTER UPDATE OF nom, brief ON projets_recherche
FOR EACH ROW EXECUTE FUNCTION invalider_configuration_projet();

CREATE FUNCTION invalider_suppression_projet() RETURNS TRIGGER AS $$
BEGIN
    DELETE FROM correspondances_calculees WHERE produit_id = OLD.produit_id;
    DELETE FROM calculs_transverses WHERE produit_id = OLD.produit_id;
    RETURN OLD;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER projets_invalidation_delete
BEFORE DELETE ON projets_recherche
FOR EACH ROW EXECUTE FUNCTION invalider_suppression_projet();

CREATE VIEW features_embeddables AS
    SELECT source, source_id AS id, nom_generique AS texte, embedding,
           transcript_id, COALESCE(verbatim, texte_original) AS verbatim, produit_id
    FROM besoins_detectes
    WHERE statut = 'extrait' AND trim(nom_generique) <> '';

INSERT INTO produits (nom) VALUES ('MQC'), ('MSC'), ('MSS');

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
