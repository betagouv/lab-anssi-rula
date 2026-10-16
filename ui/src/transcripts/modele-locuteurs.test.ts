import { describe, expect, it } from 'vitest';
import { decouperLocuteurs } from './modele-locuteurs';

describe('decouperLocuteurs', () => {
  it('isole les libellés des locuteurs du texte libre', () => {
    const locuteurs = [
      {
        identifiant: 'SPEAKER_01',
        role: 'interne' as const,
        justification: '',
      },
      {
        identifiant: 'SPEAKER_04',
        role: 'indetermine' as const,
        justification: '',
      },
    ];

    expect(
      decouperLocuteurs(
        'SPEAKER_01: Bonjour\nSPEAKER_04: Oui\nSPEAKER_04: encore',
        locuteurs
      )
    ).toEqual([
      { type: 'locuteur', identifiant: 'SPEAKER_01', texte: 'Interne · 1' },
      { type: 'texte', texte: ' Bonjour\n' },
      { type: 'locuteur', identifiant: 'SPEAKER_04', texte: 'Indéterminé · 4' },
      { type: 'texte', texte: ' Oui\n' },
      { type: 'locuteur', identifiant: 'SPEAKER_04', texte: 'Indéterminé · 4' },
      { type: 'texte', texte: ' encore' },
    ]);
  });

  it('répète le nom saisi pour toutes les mentions du speaker', () => {
    const segments = decouperLocuteurs('SPEAKER_04: Oui\nSPEAKER_04: encore', [
      {
        identifiant: 'SPEAKER_04',
        role: 'indetermine',
        justification: '',
        nom_affiche: 'Ada',
      },
    ]);

    expect(segments.filter((segment) => segment.type === 'locuteur')).toEqual([
      { type: 'locuteur', identifiant: 'SPEAKER_04', texte: 'Ada' },
      { type: 'locuteur', identifiant: 'SPEAKER_04', texte: 'Ada' },
    ]);
  });
});
