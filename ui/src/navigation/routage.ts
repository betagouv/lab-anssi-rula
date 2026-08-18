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

export function vueDepuisHash(hash: string): Vue {
  const segments = segmentsDepuisHash(hash);
  const [premier, second, troisieme, quatrieme] = segments;

  if (premier === 'sources') {
    if (second === 'entretiens') {
      const id = entierPositif(troisieme);
      if (id && quatrieme === 'modifier') {
        return { nom: 'sources:entretiens:modification', id };
      }
      if (id && !quatrieme) return { nom: 'sources:entretiens:detail', id };
      if (troisieme === 'ajout' && !quatrieme) {
        return { nom: 'sources:entretiens:ajout' };
      }
      if (!troisieme) return { nom: 'sources:entretiens' };
    }
    if (second === 'retours-bizdev' && !troisieme) {
      return { nom: 'sources:retours-bizdev' };
    }
    if (second === 'retours-bizdev') {
      const id = entierPositif(troisieme);
      if (id && !quatrieme) return { nom: 'sources:retours-bizdev:detail', id };
    }
    if (second === 'featurebase' && !troisieme) {
      return { nom: 'sources:featurebase' };
    }
    if (second === 'featurebase') {
      const id = entierPositif(troisieme);
      if (id && !quatrieme) return { nom: 'sources:featurebase:detail', id };
    }
  }

  if (premier === 'analyses' && !second) return { nom: 'analyses' };
  if (premier === 'besoins' && !second) return { nom: 'besoins' };

  // Compatibilité avec la première version de l'arborescence.
  if (premier === 'syntheses') {
    if (second === 'analyses' && !troisieme) return { nom: 'analyses' };
    if (second === 'besoins' && !troisieme) return { nom: 'besoins' };
  }

  if (premier === 'correspondances' && !second) {
    return { nom: 'correspondances' };
  }

  // Compatibilité avec les anciens liens internes et favoris.
  if (premier === 'transcripts') {
    const id = entierPositif(second);
    if (id && troisieme === 'modification') {
      return { nom: 'sources:entretiens:modification', id };
    }
    if (id) return { nom: 'sources:entretiens:detail', id };
    return { nom: 'sources:entretiens' };
  }
  if (premier === 'analyses') return { nom: 'analyses' };
  if (premier === 'fonctionnalites') return { nom: 'sources:featurebase' };
  if (premier === 'retours-bizdev') return { nom: 'sources:retours-bizdev' };
  if (premier === 'correspondance') return { nom: 'correspondances' };

  return ROUTE_PAR_DEFAUT;
}

export function hashDepuisVue(vue: Vue): string {
  switch (vue.nom) {
    case 'sources:entretiens':
      return '#sources/entretiens';
    case 'sources:entretiens:ajout':
      return '#sources/entretiens/ajout';
    case 'sources:entretiens:detail':
      return `#sources/entretiens/${vue.id}`;
    case 'sources:entretiens:modification':
      return `#sources/entretiens/${vue.id}/modifier`;
    case 'sources:retours-bizdev':
      return '#sources/retours-bizdev';
    case 'sources:retours-bizdev:detail':
      return `#sources/retours-bizdev/${vue.id}`;
    case 'sources:featurebase':
      return '#sources/featurebase';
    case 'sources:featurebase:detail':
      return `#sources/featurebase/${vue.id}`;
    case 'analyses':
      return '#analyses';
    case 'besoins':
      return '#besoins';
    case 'correspondances':
      return '#correspondances';
  }
}
