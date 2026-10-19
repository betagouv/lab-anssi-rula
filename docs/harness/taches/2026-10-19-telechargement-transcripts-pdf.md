# Tâche : télécharger le transcript pseudonymisé en PDF

Statut : prête à revoir

## Objectif

Permettre de télécharger et partager le transcript confirmé d’un entretien produit ou d’un retour BizDev sans conserver ni réexposer le PDF source.

## Périmètre

- Inclus : export PDF du contenu confirmé et pseudonymisé, téléchargement depuis la liste des sources et la relecture enregistrée, actualisation de la liste après confirmation.
- Exclu : analyses générées, PDF source, correspondances d’anonymisation, justifications des locuteurs, export groupé.

## Critères d’acceptation

- [x] Chaque transcript confirmé de type produit ou BizDev est exportable sans analyse ni appel à Albert.
- [x] Le lien est présent dans chaque ligne de la liste et à droite de « Modifier » dans la relecture enregistrée; les modifications non enregistrées ne sont pas exportées.
- [x] Une confirmation ou mise à jour réussie actualise la liste sans recharger l’écran.
- [x] Le PDF A4 contient le type, la date, le contenu pseudonymisé complet, les libellés stables des locuteurs et le contexte facultatif; le contexte n’inclut aucune justification.
- [x] Les accents, apostrophes, caractères HTML littéraux, paragraphes et textes longs restent lisibles sur toutes les pages.
- [x] Le téléchargement porte le nom ASCII attendu, `application/pdf`, `Cache-Control: no-store` et `X-Content-Type-Options: nosniff`; une source absente retourne 404 sans cache.
- [x] Les commandes complètes du harness et son audit passent; le parcours est vérifié en navigateur sur mobile et bureau.
- [x] Le changement de hash Produit ↔ BizDev recrée le composant; la liste et le détail ne reprennent pas l’état de l’autre type.

## Plan

1. Générer le PDF depuis le DTO confirmé avec ReportLab et la police Vera distribuée sous sa licence par ReportLab.
2. Ajouter une route de téléchargement dépendant directement du dépôt de transcripts.
3. Ajouter les liens DSFR aux deux emplacements et recharger la liste après chaque sauvegarde réussie.
4. Ajouter les tests du rendu multipage et du contrat HTTP.
5. Vérifier un service de démonstration isolé, les contrôles requis et la revue Sol.

## Validation

- Commandes ciblées pendant l’itération :
- `bash scripts/harness.sh complet` : réussite; Ruff, mypy, pytest (338 réussis, 2 ignorés), Svelte/TypeScript, 101 tests UI, ESLint, Prettier et build Vite.
- `bash scripts/harness.sh audit` : code 0; 12 signalements Bandit existants dans `src/infra/postgres/depot_projets.py`, `src/infra/postgres/depot_transcripts_pdf.py` et `src/transcripts_pdf/service.py`; aucun dans le nouveau code d’export.
- Parcours réel isolé : produit 4, projet « Recette export PDF », import, pseudonymisation et confirmation par Albert, apparition immédiate en liste, puis téléchargement du transcript confirmé sans analyse. Base Postgres jetable sur `127.0.0.1:55433`, volume sous `D:/Codex/rula-transcripts-pdf-export/postgres-data`; aucune base existante modifiée.
- Rendu vérifié : `D:/Codex/rula-transcripts-pdf-export/rendu/produit-page-1.png`; capture du parcours : `D:/Codex/rula-transcripts-pdf-export/rendu/parcours-reel-desktop.jpg`.

## Décisions

- ADR associée ou « aucune » : aucune.
- Source du PDF : objet persistant confirmé, jamais préparation, analyse ou document d’origine.
- Police intégrée : Bitstream Vera fournie avec ReportLab; sa licence est incluse dans la distribution Python.
- D7 : changement de Produit ↔ BizDev réinitialise le composant `ImportTranscriptPdf`, y compris ses sources et son transcript courant.

## Handoff

- État du code : revue Sol acceptée; contrôles requis verts.
- Prochaine action : commit, push, ouverture de la PR, vérification CI, puis fusion et déploiement DEMO selon l’autorisation explicite de l’utilisateur.
- Risques ou limites : l’audit Qlty conserve ses 12 constats Bandit historiques; les 2 tests d’intégration PostgreSQL existants restent ignorés par le harness.

## Revue indépendante

- Diff examiné : revu par Sol après correction de l’affichage numérique du rôle de locuteur.
- Critères vérifiés : parcours réel Produit, import Albert, confirmation, actualisation de liste et export après modification enregistrée; échange Produit ↔ BizDev; vérifications visuelles desktop et mobile; API et export paginé.
- Remarques : revue Sol acceptée. L’échange de hash Produit ↔ BizDev a été vérifié; le changement entre deux produits/projets distincts n’a pas fait l’objet d’un essai navigateur dédié.
- Verdict : prêt à fusionner
