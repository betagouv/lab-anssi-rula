# Harness local

Le harness organise le travail assisté par LLM sans orchestrateur ni service distant.

- `modeles/fiche-de-tache.md` définit le contrat, les preuves et le handoff d'une tâche.
- `taches/` conserve les fiches de tâches réalisées.
- `../adr/` conserve les décisions techniques durables.

Le déroulé est : planifier une tâche bornée, implémenter, exécuter `rapide` pendant l'itération, exécuter `complet` et `audit` avant PR, puis faire relire le diff par un rôle distinct. La décision de fusion reste humaine.
