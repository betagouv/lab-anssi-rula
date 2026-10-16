import { describe, expect, it } from 'vitest';
import {
  CATEGORIES_PSEUDONYMISATION,
  decouperTranscriptPseudonymise,
} from './marqueurs-pseudonymisation';

describe('découpage du transcript pseudonymisé', () => {
  it('reconnaît les six catégories persistées', () => {
    const texte = CATEGORIES_PSEUDONYMISATION.map(
      (categorie) => `[${categorie.code}_02]`
    ).join(' ');
    const segments = decouperTranscriptPseudonymise(texte);

    expect(
      segments
        .map((segment) => segment.categorie?.id)
        .filter((id) => id !== undefined)
    ).toEqual(CATEGORIES_PSEUDONYMISATION.map((categorie) => categorie.id));
    expect(segments.map((segment) => segment.texte).join('')).toBe(texte);
  });

  it('préserve exactement le texte, les locuteurs, les accents et les lignes', () => {
    const texte =
      'Interne · 1: Zoé cite [IDENTITE_02].\nExterne · 1: secret [SECRET_100].';
    const segments = decouperTranscriptPseudonymise(texte);

    expect(segments.map((segment) => segment.texte).join('')).toBe(texte);
    expect(segments.filter((segment) => segment.categorie)).toHaveLength(2);
  });

  it('laisse les marqueurs inconnus et le HTML en texte ordinaire', () => {
    const texte = '<script>texte</script> [INCONNU_01] [identite_01]';
    const segments = decouperTranscriptPseudonymise(texte);

    expect(segments).toEqual([{ texte, categorie: null }]);
  });

  it('renvoie une liste vide pour un transcript vide', () => {
    expect(decouperTranscriptPseudonymise('')).toEqual([]);
  });
});
