# ADR 0002 : Retours d’erreur explicites

Date : 2026-09-04

## Contexte

Les erreurs d’Albert pouvaient remonter jusqu’au frontend sans contrat stable.
Une réponse HTML du backend était alors interprétée comme du JSON et affichait
`Unexpected token '<'`. Les formulaires de transcript pouvaient aussi atteindre
le service de validation avec des champs obligatoires absents ou blancs. La
création d’un projet n’imposait pas encore explicitement son nom et son brief.

## Décision

Les appels à Albert utilisent une hiérarchie d’exceptions typées :
communication, délai dépassé, réponse HTTP et réponse invalide. Le client fixe
le timeout à 30 secondes et ne réessaie pas automatiquement.

FastAPI convertit ces exceptions en réponses `{"detail": ...}` avec un statut
503 pour l’indisponibilité et 502 pour une réponse distante invalide. Les erreurs
de validation de formulaire et de projet utilisent un `detail` structuré avec un
message et la liste des champs à corriger. Le frontend passe par un parseur commun qui
accepte les détails JSON structurés, les réponses HTML inattendues et les erreurs
réseau. Les erreurs de garde-fou restent exposées par leurs classes dédiées.

## Conséquences

- Bénéfice : l’utilisateur obtient une action compréhensible et les couches
  partagent un contrat d’erreur stable.
- Coût ou limite : les détails techniques de la réponse Albert ne sont pas
  exposés et un nouvel essai reste manuel.
- Alternatives écartées : afficher le statut HTTP brut, parser chaque endpoint
  séparément ou ajouter des retries automatiques.
