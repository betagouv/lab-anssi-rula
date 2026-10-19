# ADR 0004 — Rapports Claude et accès MCP

Date : 2026-10-19

## Contexte

RULA conserve des transcripts produit et BizDev confirmés, dont le contenu est déjà pseudonymisé avant enregistrement. L’utilisateur veut les ouvrir dans Claude Desktop, y faire produire une analyse, puis retrouver et relire celle-ci dans RULA. L’intégration ne doit pas déclencher Albert ni remplacer ses analyses existantes. Les rapports doivent rester traçables à une révision exacte de leur source.

## Décision

Ajouter une table additive `rapports_claude` liée aux transcripts par clé étrangère avec suppression en cascade. Chaque rapport conserve la révision, une empreinte SHA-256 canonique de la source, une clé UUID d’idempotence et le Markdown produit. Les rapports ne sont jamais mis à jour; leur statut courant est dérivé de la révision, que le dépôt PDF incrémente lors des modifications applicatives. L’empreinte vérifie les écritures et lectures de source par blocs.

Expose les lectures dans l’API RULA et réserve l’écriture à trois outils MCP : `lister_transcripts`, `lire_transcript` et `enregistrer_analyse`. Le POC local n’a pas d’authentification applicative; tout accès public de l’API exige la protection HTTP Basic Clever déjà documentée. Le transport local stdio destiné à Claude Desktop utilise les dépôts PostgreSQL RULA. Le transport HTTP stateless partage la factory d’outils, protège toutes les routes hors santé minimale par bearer et échoue au démarrage si le secret est absent. Les sources ne sortent que par blocs bornés et les lectures multi-blocs sont liées à la révision et à l’empreinte du premier bloc.

Le catalogue ne divulgue ni titre, ni fichier, ni nom de produit. Les sources éligibles sont seulement les transcripts confirmés de type `produit` ou `bizdev`. Le workflow Clever Cloud est manuel, utilise une application et des secrets distincts de DEMO et n’est pas exécuté par cette tâche.

## Conséquences

- Bénéfice : une analyse externe peut être enregistrée et relue dans RULA avec provenance et détection d’obsolescence, sans altérer les résultats Albert.
- Coût ou limite : une nouvelle migration additive, des interfaces de dépôt dédiées et deux transports MCP doivent être maintenus. Les modifications manuelles en base qui ne changent pas la révision sont hors du contrat applicatif.
- Alternatives écartées : remplacer les analyses Albert, stocker les rapports dans le texte du transcript, fournir l’écriture REST ou exposer des transcripts non confirmés.
