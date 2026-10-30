import { render } from 'svelte/server';
import { describe, expect, it } from 'vitest';
import ConfirmationPseudonymisation from './ConfirmationPseudonymisation.svelte';

describe('confirmation de pseudonymisation', () => {
  it('annonce la perte des correspondances et la conservation des termes de liste noire', () => {
    const { body } = render(ConfirmationPseudonymisation, {
      props: {
        modalId: 'confirmation-test',
        confirmationNecessaire: true,
        desactive: false,
        enCours: false,
        erreur: '',
        onconfirmer: async () => true,
      },
    });

    expect(body).toContain('aria-haspopup="dialog"');
    expect(body).toContain('class="fr-modal"');
    expect(body).toContain('Confirmer la pseudonymisation définitive');
    expect(body).toContain('ne seront pas conservées');
    expect(body).toContain('Les termes de la liste noire restent');
    expect(body).toContain('associés à la source');
    expect(body).toContain('Confirmer et enregistrer');
    expect(body).toContain('Retour à la relecture');
  });
});
