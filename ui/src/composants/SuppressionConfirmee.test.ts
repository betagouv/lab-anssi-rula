import { render } from 'svelte/server';
import { describe, expect, it } from 'vitest';
import SuppressionConfirmee from './SuppressionConfirmee.svelte';

describe('confirmation de suppression', () => {
  it('exige le texte exact avant de pouvoir confirmer', () => {
    const { body } = render(SuppressionConfirmee, {
      props: {
        modalId: 'suppression-test',
        titre: 'Supprimer ce transcript ?',
        description: 'Le transcript et son analyse seront supprimés.',
        onconfirmer: async () => {},
        onsucces: () => {},
      },
    });

    expect(body).toContain('Saisissez exactement JE CONFIRME');
    expect(body).toContain('disabled');
    expect(body).toContain('class="fr-modal"');
    expect(body).toContain('data-fr-opened="false"');
  });
});
