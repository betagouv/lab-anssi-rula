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
