import { render } from 'svelte/server';
import { describe, expect, it } from 'vitest';
import RemplacementsTranscript from './RemplacementsTranscript.svelte';

describe('rendu des remplacements transcript', () => {
  it('avertit seulement quand des plages contradictoires ont été fusionnées', () => {
    const aucun = render(RemplacementsTranscript, {
      props: { remplacements: [], conflitsCategoriesFusionnes: 0 },
    });
    expect(aucun.body).not.toContain('zone de chevauchement');

    const fusion = render(RemplacementsTranscript, {
      props: { remplacements: [], conflitsCategoriesFusionnes: 2 },
    });
    expect(fusion.body).toContain('2 zones de chevauchement ont été fusionnées');
    expect(fusion.body).toContain('relisez le brouillon avant de le confirmer');
  });

  it('affiche deux occurrences de même champ et valeur dans des catégories distinctes', () => {
    const { body } = render(RemplacementsTranscript, {
      props: {
        remplacements: [
          {
            champ: 'transcript',
            valeur_originale: 'EXEMPLE NOM',
            valeur_anonyme: 'PERSONNE_01',
            categorie: 'nom',
          },
          {
            champ: 'transcript',
            valeur_originale: 'EXEMPLE NOM',
            valeur_anonyme: 'ORGANISATION_01',
            categorie: 'organisation',
          },
        ],
      },
    });
    expect(body.match(/<tr/g)).toHaveLength(3);
    expect(body).toContain('PERSONNE_01');
    expect(body).toContain('ORGANISATION_01');
    expect(body).toContain('nom');
    expect(body).toContain('organisation');
  });
});
