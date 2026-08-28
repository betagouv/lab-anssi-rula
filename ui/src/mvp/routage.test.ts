import { describe, expect, it } from 'vitest';
import { routeMvp } from './routage';

describe('routage MVP', () => {
  it.each([
    ['#/', { nom: 'entree' }],
    ['#/produits/2/dashboard', { nom: 'dashboard', produitId: 2 }],
    ['#/produits/2/projets', { nom: 'projets', produitId: 2 }],
    ['#/produits/2/nouveau', { nom: 'nouveau', produitId: 2 }],
    ['#/projets/4', { nom: 'projet', projetId: 4 }],
    ['#/projets/4/scan', { nom: 'scan', projetId: 4 }],
    ['#/projets/4/configuration', { nom: 'configuration', projetId: 4 }],
    ['#/projets/4/detail', { nom: 'detail', projetId: 4 }],
  ])('lit %s', (hash, attendu) => expect(routeMvp(hash)).toEqual(attendu));

  it.each(['#/produits/0/dashboard', '#/projets/x', '#/inconnu'])(
    'refuse %s',
    (hash) => expect(routeMvp(hash)).toBeNull()
  );
});
