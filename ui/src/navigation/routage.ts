import type { Vue } from '../types';

export const ROUTE_PAR_DEFAUT: Vue = { nom: 'sources:entretiens' };

function entierPositif(value: string | undefined): number | null {
  if (!value || !/^\d+$/.test(value)) return null;
  const id = Number(value);
  return Number.isSafeInteger(id) && id > 0 ? id : null;
}

function segmentsDepuisHash(hash: string): string[] {
  return hash.replace(/^#\/?/, '').replace(/\/+$/, '').split('/');
}

function vueDepuisEntretiens(
  troisieme: string | undefined,
  quatrieme: string | undefined
): Vue | undefined {
  const id = entierPositif(troisieme);
  if (id && quatrieme === 'modifier')
    return { nom: 'sources:entretiens:modification', id };
  if (id && !quatrieme) return { nom: 'sources:entretiens:detail', id };
  if (troisieme === 'ajout' && !quatrieme)
    return { nom: 'sources:entretiens:ajout' };
  return !troisieme ? { nom: 'sources:entretiens' } : undefined;
}

function vueDepuisSource(
  nom: string | undefined,
  troisieme: string | undefined,
  quatrieme: string | undefined
): Vue | undefined {
  const routes: Record<string, Vue> = {
    'retours-bizdev': { nom: 'sources:retours-bizdev' },
    featurebase: { nom: 'sources:featurebase' },
  };
  if (!troisieme) return routes[nom ?? ''];
  const id = entierPositif(troisieme);
  if (id && !quatrieme && nom === 'retours-bizdev')
    return { nom: 'sources:retours-bizdev:detail', id };
  return id && !quatrieme && nom === 'featurebase'
    ? { nom: 'sources:featurebase:detail', id }
    : undefined;
}

function vueDepuisSources(segments: string[]): Vue | undefined {
  const [premier, second, troisieme, quatrieme] = segments;
  if (premier !== 'sources') return undefined;
  if (second === 'entretiens') return vueDepuisEntretiens(troisieme, quatrieme);
  return vueDepuisSource(second, troisieme, quatrieme);
}

function vueDepuisAnciensLiens(segments: string[]): Vue | undefined {
  const [premier, second, troisieme] = segments;
  if (premier === 'syntheses' && second === 'analyses' && !troisieme)
    return { nom: 'analyses' };
  if (premier === 'transcripts') {
    const id = entierPositif(second);
    if (id)
      return {
        nom:
          troisieme === 'modification'
            ? 'sources:entretiens:modification'
            : 'sources:entretiens:detail',
        id,
      };
    return { nom: 'sources:entretiens' };
  }
  const aliases: Record<string, Vue> = {
    analyses: { nom: 'analyses' },
    'retours-bizdev': { nom: 'sources:retours-bizdev' },
  };
  return aliases[premier ?? ''];
}

export function vueDepuisHash(hash: string): Vue {
  const segments = segmentsDepuisHash(hash);
  return (
    vueDepuisSources(segments) ?? vueDepuisAnciensLiens(segments) ?? ROUTE_PAR_DEFAUT
  );
}

function idDepuisVue(vue: Vue): number {
  return 'id' in vue ? vue.id : 0;
}

const HASH_PAR_NOM: Record<Vue['nom'], (vue: Vue) => string> = {
  'sources:entretiens': () => '#sources/entretiens',
  'sources:entretiens:ajout': () => '#sources/entretiens/ajout',
  'sources:entretiens:detail': (vue) => `#sources/entretiens/${idDepuisVue(vue)}`,
  'sources:entretiens:modification': (vue) =>
    `#sources/entretiens/${idDepuisVue(vue)}/modifier`,
  'sources:retours-bizdev': () => '#sources/retours-bizdev',
  'sources:retours-bizdev:detail': (vue) =>
    `#sources/retours-bizdev/${idDepuisVue(vue)}`,
  'sources:featurebase': () => '#sources/featurebase',
  'sources:featurebase:detail': (vue) => `#sources/featurebase/${idDepuisVue(vue)}`,
  analyses: () => '#analyses',
};

export function hashDepuisVue(vue: Vue): string {
  return HASH_PAR_NOM[vue.nom](vue);
}
