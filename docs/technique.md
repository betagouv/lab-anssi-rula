# RULA — Document technique du POC

> **RULA** : Research User Listening & Analysis
> **Date** : 2026-06-16
> **Statut** : POC — ne pas confondre avec un MVP ou un produit

---

## Besoin produit (reformulé)

Les équipes Product et BizDev d'un éditeur de service public numérique collectent des verbatims utilisateurs via deux canaux :

- **Transcripts d'entretiens utilisateurs** (User Research, Bizdev) — textes longs, structurés autour d'une session.
- **Idées et feedbacks** issus d'outils comme Feature Base — items courts, catégorisés.

Aujourd'hui, ces données sont stockées de façon dispersée (fichiers, tableurs, outils tiers), ce qui rend difficile :

1. La capitalisation et la recherche transversale sur plusieurs sessions.
2. L'identification des sujets récurrents et leur regroupement en **Meta-Features** (ex : cinq formulations différentes d'un même besoin → une seule Meta-Feature consolidée).
3. L'analyse sur une période de temps donnée pour un produit donné.

**RULA** propose une interface simple pour déposer, gérer et analyser ces transcripts, avec une couche d'analyse LLM pour faire émerger automatiquement les patterns.

---

## 1. Hypothèse principale à valider

> **Un LLM peut, à partir d'un corpus de transcripts non structurés, identifier et regrouper de façon fiable les sujets récurrents en Meta-Features, avec un niveau de pertinence suffisant pour remplacer ou accélérer significativement le travail manuel de dépouillement.**

Hypothèse secondaire : l'interface d'upload + consultation est suffisamment simple pour être adoptée sans formation par les PO/BizDev.

---

## 2. Critères de succès du POC

| Critère | Mesure | Seuil |
|---|---|---|
| Pertinence des Meta-Features générées | Évaluation manuelle sur un corpus test (transcripts réels fournis) | ≥ 70 % jugées « pertinentes » ou « partiellement pertinentes » par l'équipe |
| Couverture | Proportion de sujets importants capturés | ≥ 80 % des sujets identifiés manuellement retrouvés |
| Latence d'analyse | Temps de traitement d'un corpus de 10 transcripts | < 60 secondes |
| Adoption interface | Upload et consultation par un utilisateur non-technique sans aide | Scénario complété en < 5 min |

---

## 3. Risques

| Risque | Probabilité | Impact | Mitigation |
|---|---|---|---|
| Hallucinations LLM sur les regroupements | Moyenne | Fort | Afficher la liste des verbatims sources pour chaque Meta-Feature ; permettre la correction manuelle |
| Qualité variable des transcripts (longueur, format) | Forte | Moyen | Normalisation légère à l'import (strip, encodage) ; pas de parser complexe dans le POC |
| Coût API LLM sur gros corpus | Faible (POC) | Moyen | Budgéter l'analyse par batch ; alerter si > N tokens estimés |
| Confidentialité des verbatims | Forte | Fort | Périmètre POC = local uniquement ; pas de données réelles en production avant audit |
| Scope creep vers un produit complet | Forte | Fort | Périmètre strict défini ci-dessous ; PRD différé |

---

## 4. Périmètre strict du POC

### Dans le périmètre

- Upload de transcripts (texte brut ou `.txt` / `.md`) via une UI minimaliste.
- Stockage en base PostgreSQL (table `transcripts`).
- Modification et suppression d'un transcript.
- Sélection d'un produit et d'une plage de dates → déclenchement d'une analyse.
- Analyse : extraction des sujets récurrents + regroupement en Meta-Features (via LLM).
- Affichage des résultats : liste des Meta-Features, occurrences, verbatims associés.
- Authentification : **aucune pour le POC** (accès local uniquement).

### Hors périmètre (décidé délibérément)

- Anonymisation des transcripts (postulat : les fichiers déposés sont déjà anonymisés).
- Intégration Feature Base (lecture seule possible plus tard, pas dans le POC).
- ProConnect (prévu si POC concluant).
- Analyse sémantique avancée (embeddings, RAG, clustering vectoriel) — on commence par un prompt LLM direct.
- Multi-tenant, gestion de rôles, audit log.
- Export PDF / rapport formaté.

---

## 5. Plan d'implémentation incrémental

### Étape 0 — Socle (Jour 1)

- [ ] Initialiser le projet Python avec `uv` + `pyproject.toml`.
- [ ] Initialiser le frontend Svelte 5 avec `pnpm`.
- [ ] Configurer `docker-compose` : PostgreSQL + backend FastAPI + frontend Vite.
- [ ] Fichier `.env.template` avec les variables attendues.
- [ ] Migration SQL initiale : table `transcripts`, table `produits`.

### Étape 1 — CRUD Transcripts (Jour 2)

- [ ] Route `POST /api/transcripts` — upload d'un transcript (titre, produit, date, contenu texte).
- [ ] Route `GET /api/transcripts` — liste avec filtre produit + plage de dates.
- [ ] Route `PUT /api/transcripts/{id}` — modification.
- [ ] Route `DELETE /api/transcripts/{id}` — suppression.
- [ ] UI : page liste + formulaire upload + actions modifier/supprimer.
- [ ] Tests : routes CRUD avec base de test (pytest + fixture PostgreSQL).

### Étape 2 — Analyse LLM (Jour 3-4)

- [ ] Route `POST /api/analyses` — déclenche l'analyse sur un corpus (produit + plage).
- [ ] Prompt LLM : extraction des sujets → regroupement en Meta-Features → retour JSON structuré.
- [ ] Stockage du résultat d'analyse en base (table `analyses`, table `meta_features`).
- [ ] UI : page résultats — liste Meta-Features, compteur d'occurrences, verbatims sources.
- [ ] Tests : mock LLM pour valider la chaîne de traitement sans appel API réel.

### Étape 3 — Validation métier (Jour 5)

- [ ] Session de test avec l'équipe sur corpus réel (transcripts fournis).
- [ ] Recueil des retours qualitatifs sur la pertinence des Meta-Features.
- [ ] Identification des ajustements de prompt si nécessaire.
- [ ] Documentation des limites observées.

---

## Stack technique

Alignée sur le repo `anssi-recommandations-cyber-data` :

| Couche | Choix | Justification |
|---|---|---|
| Langage backend | Python 3.13 | Cohérence avec la stack existante |
| Framework API | FastAPI | Cohérence, async natif |
| Gestionnaire de paquets | `uv` | Cohérence |
| Base de données | PostgreSQL | Cohérence ; SQL brut via `psycopg2` |
| LLM | OpenAI (`gpt-4o-mini` par défaut) ou Albert | `openai` déjà dans la stack |
| Frontend | Svelte 5 + TypeScript | Cohérence |
| Build frontend | Vite + `pnpm` | Cohérence |
| Tests backend | `pytest` + `pytest-asyncio` | Cohérence |
| Tests frontend | `vitest` | Cohérence |
| Linting | `ruff` (Python) + ESLint + Prettier | Cohérence |
| Conteneurisation | Docker + docker-compose | Cohérence |

---

## Limites documentées du POC

1. **Pas d'authentification** : le POC tourne en local. Ne jamais exposer sans auth.
2. **Transcripts supposés anonymisés** : aucune vérification ni anonymisation automatique.
3. **Analyse LLM non déterministe** : deux analyses sur le même corpus peuvent produire des résultats légèrement différents.
4. **Volume limité** : pas de pagination ni de gestion de corpus > quelques dizaines de transcripts testée.
5. **Pas de gestion multi-produit fine** : les produits sont de simples labels texte sans hiérarchie.
6. **Coût LLM non optimisé** : pas de cache, pas de déduplication des appels.
