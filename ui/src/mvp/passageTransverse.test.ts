import { describe, expect, it } from 'vitest';
import type { PassageTransverse } from '../api/analyse_transverse';
import { libelleSource, lienPassage } from './passageTransverse';

const passage: PassageTransverse = {
  source: 'transcript_produit',
  source_id: 17,
  transcript_id: 17,
  projet_id: 4,
  texte_normalise: 'Gérer les contributeurs',
  verbatim: 'Je veux gérer les contributeurs.',
};

describe('passage transverse de transcript produit', () => {
  it('identifie la source comme un transcript produit', () => {
    expect(libelleSource(passage.source)).toBe('Transcript produit');
  });

  it('ouvre l’entretien qui contient le transcript et son verbatim', () => {
    expect(lienPassage(passage, 3)).toBe('#/produits/3/transcripts/produit/17');
  });
});
