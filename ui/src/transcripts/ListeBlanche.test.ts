import { render } from 'svelte/server';
import { describe, expect, it } from 'vitest';
import ListeBlanche from './ListeBlanche.svelte';

describe('page de liste blanche', () => {
  it('explique sa portée et expose les actions de gestion', () => {
    const { body } = render(ListeBlanche);
    const texte = body.replace(/\s+/g, ' ');

    expect(texte).toContain('Liste blanche');
    expect(texte).toContain('prochaines préparations PDF');
    expect(texte).toContain('La relecture permet toujours d’ajouter un masque');
    expect(texte).toContain('Ajouter un terme');
    expect(texte).toContain('Retour à l’accueil');
  });
});
