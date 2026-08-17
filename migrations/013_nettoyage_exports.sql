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
