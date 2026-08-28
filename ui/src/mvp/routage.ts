type RouteProduit = {
  nom: 'dashboard' | 'projets' | 'nouveau';
  produitId: number;
};

type RouteProjet = {
  nom: 'projet' | 'configuration' | 'scan' | 'detail';
  projetId: number;
};

export type RouteMvp = { nom: 'entree' } | RouteProduit | RouteProjet;

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
    ['dashboard', 'projets', 'nouveau'].includes(segments[2] ?? '') &&
    segments.length === 3
  )
    return { nom: segments[2] as RouteProduit['nom'], produitId };
  const projetId = id(segments[1]);
  if (
    segments[0] === 'projets' &&
    projetId &&
    ['projet', 'configuration', 'scan', 'detail'].includes(segments[2] ?? '') &&
    segments.length === 3
  )
    return { nom: segments[2] as RouteProjet['nom'], projetId };
  if (segments[0] === 'projets' && projetId && segments.length === 2)
    return { nom: 'projet', projetId };
  return null;
}
