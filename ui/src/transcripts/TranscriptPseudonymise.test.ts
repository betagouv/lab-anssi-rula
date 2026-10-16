import { render } from 'svelte/server';
import { describe, expect, it } from 'vitest';
import TranscriptPseudonymise from './TranscriptPseudonymise.svelte';

describe('rendu du transcript pseudonymisé', () => {
  it('colore les pseudonymes et conserve le texte sélectionnable enregistré', () => {
    const contenu =
      'Interne · 1: Zoé [IDENTITE_02]\nExterne · 1: [TECHNOLOGIE_OU_PRODUIT_01]';
    const { body } = render(TranscriptPseudonymise, { props: { contenu } });

    expect(body).toContain('id="titre-transcript-pseudonymise"');
    expect(body).toContain('pseudonyme--identite');
    expect(body).toContain('pseudonyme--technologie-ou-produit');
    expect(body).toContain('Identité');
    expect(body).toContain('Technologie ou produit');
    expect(body).toContain('[IDENTITE_02]');
    expect(body).toContain('[TECHNOLOGIE_OU_PRODUIT_01]');
    expect(body).toContain('Zoé');
  });

  it('échappe les valeurs affichées et garde le texte intact', () => {
    const contenu = '<script>Zoé</script> [IDENTITE_02]';
    const { body } = render(TranscriptPseudonymise, { props: { contenu } });

    expect(body).toContain('&lt;script>Zoé&lt;/script>');
    expect(body).not.toContain('<script>');
    expect(body).toContain('[IDENTITE_02]');
  });
});
