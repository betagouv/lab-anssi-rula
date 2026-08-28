type RouteProduit = {
  nom: 'dashboard' | 'projets' | 'nouveau' | 'source' | 'source-liste';
  produitId: number;
  source?: 'transcript' | 'bizdev' | 'featurebase';
};

type RouteProjet = {
  nom: 'projet' | 'configuration' | 'analyse' | 'scan' | 'detail';
  projetId: number;
  etape?: string;
};

type RouteEntretien = {
  nom: 'entretien';
  projetId: number;
  entretienId: number;
};

type RouteSourceProjet = {
  nom: 'source-projet';
  projetId: number;
  source: 'bizdev' | 'featurebase';
};

export type RouteMvp =
  | { nom: 'entree' }
  | RouteProduit
  | RouteProjet
  | RouteEntretien
  | RouteSourceProjet;

function id(value: string | undefined): number | null {
  const nombre = Number(value);
  return Number.isSafeInteger(nombre) && nombre > 0 ? nombre : null;
}

export function routeMvp(hash: string): RouteMvp | null {
  const segments = hash.replace(/^#\/?/, '').split('/').filter(Boolean);
  if (!segments.length) return { nom: 'entree' };
  const produitId = id(segments[1]);
  if (
    segments[0] === 'produits' &&
    produitId &&
    segments[2] === 'donnees' &&
    segments.length === 4 &&
    ['bizdev', 'featurebase'].includes(segments[3] ?? '')
  )
    return {
      nom: 'source-liste',
      produitId,
      source: segments[3] as RouteProduit['source'],
    };
  if (
    segments[0] === 'produits' &&
    produitId &&
    ['dashboard', 'projets', 'nouveau'].includes(segments[2] ?? '') &&
    segments.length === 3
  )
    return { nom: segments[2] as RouteProduit['nom'], produitId };
  if (
    segments[0] === 'produits' &&
    produitId &&
    segments[2] === 'sources' &&
    segments.length === 4 &&
    ['transcript', 'bizdev', 'featurebase'].includes(segments[3] ?? '')
  )
    return {
      nom: 'source',
      produitId,
      source: segments[3] as RouteProduit['source'],
    };
  const projetId = id(segments[1]);
  const entretienId = id(segments[3]);
  if (
    segments[0] === 'projets' &&
    projetId &&
    segments[2] === 'entretiens' &&
    entretienId &&
    segments.length === 4
  )
    return { nom: 'entretien', projetId, entretienId };
  if (
    segments[0] === 'projets' &&
    projetId &&
    segments[2] === 'sources' &&
    segments.length === 4 &&
    ['bizdev', 'featurebase'].includes(segments[3] ?? '')
  )
    return {
      nom: 'source-projet',
      projetId,
      source: segments[3] as RouteSourceProjet['source'],
    };
  if (
    segments[0] === 'projets' &&
    projetId &&
    ['projet', 'configuration', 'scan', 'detail'].includes(segments[2] ?? '') &&
    segments.length === 3
  )
    return { nom: segments[2] as RouteProjet['nom'], projetId };
  if (
    segments[0] === 'projets' &&
    projetId &&
    segments[2] === 'analyse' &&
    segments.length === 4 &&
    segments[3]
  )
    return { nom: 'analyse', projetId, etape: segments[3] };
  if (segments[0] === 'projets' && projetId && segments.length === 2)
    return { nom: 'projet', projetId };
  return null;
}
