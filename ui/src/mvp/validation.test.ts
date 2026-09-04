import { describe, expect, it } from 'vitest';
import { champsEntretienManquants } from './validation';

describe('validation des entretiens', () => {
  it('accepte un entretien complet', () => {
    expect(
      champsEntretienManquants({
        participant: 'Alice',
        date_entretien: '2026-09-04',
        moderateur: 'Bob',
        contenu: 'Un besoin.',
      })
    ).toEqual([]);
  });

  it('signale les valeurs vides ou composées d’espaces', () => {
    expect(
      champsEntretienManquants({
        participant: '  ',
        date_entretien: '',
        moderateur: '\t',
        contenu: ' \n',
      })
    ).toEqual([
      'Prénom de l’utilisateur',
      'Date de l’entretien',
      'Modérateur',
      'Transcript de l’entretien',
    ]);
  });
});
