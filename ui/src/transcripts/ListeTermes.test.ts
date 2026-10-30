import { render } from 'svelte/server';
import { describe, expect, it } from 'vitest';
import ListeTermes from './ListeTermes.svelte';

describe('page de gestion des termes', () => {
  it('affiche les règles de la liste blanche', () => {
    const { body } = render(ListeTermes, { props: { couleur: 'blanche' } });
    const texte = body.replace(/\s+/g, ' ');

    expect(texte).toContain('Liste blanche');
    expect(texte).toContain('prochaines préparations PDF');
    expect(texte).toContain('La relecture permet toujours d’ajouter un masque');
    expect(texte).toContain('Ajouter un terme');
  });

  it('affiche les obligations de la liste noire', () => {
    const { body } = render(ListeTermes, { props: { couleur: 'noire' } });
    const texte = body.replace(/\s+/g, ' ');

    expect(texte).toContain('Liste noire');
    expect(texte).toContain('masqués dans les nouvelles préparations seulement');
    expect(texte).toContain('masques restent obligatoires à la relecture');
    expect(texte).toContain('Ajouter un terme à masquer');
  });
});
