import { render } from 'svelte/server';
import { describe, expect, it } from 'vitest';
import ListeNoire from './ListeNoire.svelte';

describe('page de liste noire', () => {
  it('explique sa portée et expose les actions de gestion', () => {
    const { body } = render(ListeNoire);
    const texte = body.replace(/\s+/g, ' ');

    expect(texte).toContain('Liste noire');
    expect(texte).toContain('nouvelles préparations seulement');
    expect(texte).toContain('Leurs masques restent obligatoires à la relecture');
    expect(texte).toContain('Ajouter un terme à masquer');
    expect(texte).toContain('Retour à l’accueil');
  });
});
