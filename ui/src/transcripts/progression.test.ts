import { describe, expect, it } from 'vitest';
import {
  dureeDepuisSoumission,
  libelleProgression,
  pourcentageProgression,
  type ProgressionPreparation,
} from './progression';

function progression(
  phase: ProgressionPreparation['phase'],
  termines = 0,
  total: number | null = null
): ProgressionPreparation {
  return {
    phase,
    groupes_termines: termines,
    groupes_total: total,
    groupe_en_cours: null,
    duree_secondes: 0,
  };
}

describe('progression de préparation', () => {
  it('reste indéterminée tant que le nombre de groupes est inconnu', () => {
    expect(pourcentageProgression(progression('en_attente'))).toBeNull();
    expect(pourcentageProgression(progression('extraction'))).toBeNull();
  });

  it('annonce les groupes réellement validés et laisse la finalisation indéterminée', () => {
    expect(libelleProgression(progression('anonymisation'))).toBe(
      'Anonymisation du transcript'
    );
    expect(pourcentageProgression(progression('anonymisation', 7, 18))).toBe(38);
    expect(pourcentageProgression(progression('finalisation', 18, 18))).toBeNull();
  });

  it('distingue les groupes terminés de la préparation terminée', () => {
    expect(pourcentageProgression(progression('anonymisation', 18, 18))).toBe(100);
    expect(libelleProgression(progression('anonymisation', 18, 18))).toBe(
      'Anonymisation du transcript'
    );
    expect(pourcentageProgression(progression('termine', 18, 18))).toBe(100);
  });

  it('formate le temps écoulé depuis la soumission sans estimation', () => {
    expect(dureeDepuisSoumission(17.9)).toBe('17 s');
    expect(dureeDepuisSoumission(125)).toBe('2 min 5 s');
    expect(dureeDepuisSoumission(-1)).toBe('0 s');
  });
});
