import { render } from 'svelte/server';
import { describe, expect, it } from 'vitest';
import ResultatAnalyse from './ResultatAnalyse.svelte';

describe('rendu d’une analyse de transcript PDF', () => {
  it('affiche le résumé, les verbatims et les points saillants', () => {
    const { body } = render(ResultatAnalyse, {
      props: {
        contenu: {
          resume: 'Synthèse utilisateur',
          themes: ['Gestion des droits'],
          points_positifs: [
            {
              description: 'La synthèse est pratique',
              verbatim: 'C’est très pratique.',
              speaker_id: 'SPEAKER_01',
              tour_id: 4,
              sentiment: 'positif',
              gravite: 'faible',
            },
          ],
          points_negatifs: [
            {
              description: 'La gestion est répétitive',
              sentiment: 'négatif',
              gravite: 'élevée',
            },
          ],
        },
      },
    });
    expect(body).toContain('Synthèse utilisateur');
    expect(body).toContain('Gestion des droits');
    expect(body).toContain('C’est très pratique.');
    expect(body).toContain('<p>Sentiment : positif</p>');
    expect(body).toContain('<p>Gravité : faible</p>');
    expect(body).toContain('<p>Sentiment : négatif</p>');
    expect(body).toContain('<p>Gravité : élevée</p>');
    expect(body).not.toContain('· Gravité');
  });
});
