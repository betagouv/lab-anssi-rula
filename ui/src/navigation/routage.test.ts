import { describe, expect, it } from 'vitest';
import type { Vue } from '../types';
import { hashDepuisVue, ROUTE_PAR_DEFAUT, vueDepuisHash } from './routage';

describe('routage RULA', () => {
  it.each([
    ['#sources/entretiens', { nom: 'sources:entretiens' }],
    ['#sources/entretiens/ajout', { nom: 'sources:entretiens:ajout' }],
    ['#sources/entretiens/12', { nom: 'sources:entretiens:detail', id: 12 }],
    [
      '#sources/entretiens/12/modifier',
      { nom: 'sources:entretiens:modification', id: 12 },
    ],
    ['#sources/retours-bizdev', { nom: 'sources:retours-bizdev' }],
    ['#sources/retours-bizdev/7', { nom: 'sources:retours-bizdev:detail', id: 7 }],
    ['#sources/featurebase', { nom: 'sources:featurebase' }],
    ['#sources/featurebase/9', { nom: 'sources:featurebase:detail', id: 9 }],
    ['#analyses', { nom: 'analyses' }],
  ])('parse %s', (hash, attendu) => {
    expect(vueDepuisHash(hash)).toEqual(attendu);
  });

  it.each([
    ['#transcripts', { nom: 'sources:entretiens' }],
    ['#transcripts/12', { nom: 'sources:entretiens:detail', id: 12 }],
    ['#syntheses/analyses', { nom: 'analyses' }],
    ['#retours-bizdev', { nom: 'sources:retours-bizdev' }],
  ])('conserve la compatibilité avec %s', (hash, attendu) => {
    expect(vueDepuisHash(hash)).toEqual(attendu);
  });

  it('retombe sur la route par défaut pour un hash inconnu', () => {
    expect(vueDepuisHash('#inconnu')).toEqual(ROUTE_PAR_DEFAUT);
  });

  it.each(['#fonctionnalites', '#besoins', '#correspondances'])(
    'retire la vue globale %s',
    (hash) => {
      expect(vueDepuisHash(hash)).toEqual(ROUTE_PAR_DEFAUT);
    }
  );

  it.each([
    [{ nom: 'sources:entretiens' }, '#sources/entretiens'],
    [{ nom: 'sources:entretiens:ajout' }, '#sources/entretiens/ajout'],
    [{ nom: 'sources:entretiens:detail', id: 12 }, '#sources/entretiens/12'],
    [
      { nom: 'sources:entretiens:modification', id: 12 },
      '#sources/entretiens/12/modifier',
    ],
    [{ nom: 'sources:retours-bizdev:detail', id: 7 }, '#sources/retours-bizdev/7'],
    [{ nom: 'sources:featurebase' }, '#sources/featurebase'],
    [{ nom: 'sources:featurebase:detail', id: 9 }, '#sources/featurebase/9'],
  ] as Array<[Vue, string]>)('sérialise %o', (vue, hash) => {
    expect(hashDepuisVue(vue)).toBe(hash);
  });
});
