import { describe, expect, it } from 'vitest';
import { routeMvp } from './routage';

describe('routage MVP', () => {
  it.each([
    ['#/', { nom: 'entree' }],
    ['#/produits/2/dashboard', { nom: 'dashboard', produitId: 2 }],
    ['#/produits/2/projets', { nom: 'projets', produitId: 2 }],
    ['#/produits/2/nouveau', { nom: 'nouveau', produitId: 2 }],
    [
      '#/produits/2/sources/bizdev',
      { nom: 'source', produitId: 2, source: 'bizdev' },
    ],
    [
      '#/produits/2/sources/transcript',
      { nom: 'source', produitId: 2, source: 'transcript' },
    ],
    [
      '#/produits/2/sources/featurebase',
      { nom: 'source', produitId: 2, source: 'featurebase' },
    ],
    [
      '#/produits/2/donnees/bizdev',
      { nom: 'source-liste', produitId: 2, source: 'bizdev' },
    ],
    [
      '#/produits/2/donnees/featurebase',
      { nom: 'source-liste', produitId: 2, source: 'featurebase' },
    ],
    ['#/projets/4', { nom: 'projet', projetId: 4 }],
    ['#/projets/4/entretiens/7', { nom: 'entretien', projetId: 4, entretienId: 7 }],
    [
      '#/projets/4/sources/bizdev',
      { nom: 'source-projet', projetId: 4, source: 'bizdev' },
    ],
    [
      '#/projets/4/sources/featurebase',
      { nom: 'source-projet', projetId: 4, source: 'featurebase' },
    ],
    ['#/projets/4/scan', { nom: 'scan', projetId: 4 }],
    ['#/projets/4/configuration', { nom: 'configuration', projetId: 4 }],
    [
      '#/projets/4/analyse/scan-neutre',
      { nom: 'analyse', projetId: 4, etape: 'scan-neutre' },
    ],
    ['#/projets/4/detail', { nom: 'detail', projetId: 4 }],
  ])('lit %s', (hash, attendu) => expect(routeMvp(hash)).toEqual(attendu));

  it.each(['#/produits/0/dashboard', '#/projets/x', '#/inconnu'])(
    'refuse %s',
    (hash) => expect(routeMvp(hash)).toBeNull()
  );
});
