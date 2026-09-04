export type DonneesEntretien = {
  participant: string;
  date_entretien: string;
  moderateur: string;
  contenu: string;
};

const CHAMPS = [
  ['participant', 'Prénom de l’utilisateur'],
  ['date_entretien', 'Date de l’entretien'],
  ['moderateur', 'Modérateur'],
  ['contenu', 'Transcript de l’entretien'],
] as const;

export function champsEntretienManquants(donnees: DonneesEntretien): string[] {
  return CHAMPS.filter(([champ]) => !donnees[champ].trim()).map(
    ([, libelle]) => libelle
  );
}
