export type ProgressionPreparation = {
  phase:
    | 'en_attente'
    | 'extraction'
    | 'anonymisation'
    | 'finalisation'
    | 'termine'
    | 'echec';
  groupes_termines: number;
  groupes_total: number | null;
  groupes_en_cours: number[];
  duree_secondes: number;
};

export function libelleProgression(progression: ProgressionPreparation): string {
  return {
    en_attente: 'En attente du traitement précédent',
    extraction: 'Lecture du PDF',
    anonymisation: 'Anonymisation du transcript',
    finalisation: 'Finalisation des remplacements',
    termine: 'Préparation terminée',
    echec: 'Préparation interrompue',
  }[progression.phase];
}

export function pourcentageProgression(
  progression: ProgressionPreparation
): number | null {
  if (progression.phase === 'termine') return 100;
  if (progression.phase !== 'anonymisation') return null;
  if (
    progression.phase !== 'anonymisation' ||
    progression.groupes_total === null ||
    progression.groupes_total === 0
  )
    return null;
  return Math.min(
    100,
    Math.floor((progression.groupes_termines / progression.groupes_total) * 100)
  );
}

export function dureeDepuisSoumission(secondes: number): string {
  const ecoulees = Math.max(0, Math.floor(secondes));
  const minutes = Math.floor(ecoulees / 60);
  const reste = ecoulees % 60;
  return minutes ? `${minutes} min ${reste} s` : `${reste} s`;
}

export function dureeLocale(
  secondesServeur: number,
  horodatageServeur: number,
  horodatageLocal: number
): number {
  return secondesServeur + Math.max(0, horodatageLocal - horodatageServeur) / 1000;
}
