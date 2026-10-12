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
        },
      },
    });
    expect(body).toContain('Synthèse utilisateur');
    expect(body).toContain('Gestion des droits');
    expect(body).toContain('C’est très pratique.');
    expect(body).toContain('Sentiment : positif');
    expect(body).toContain('Gravité : faible');
  });
});
