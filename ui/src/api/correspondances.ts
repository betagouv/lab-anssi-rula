import type { Cluster } from '../types';

async function json<T>(r: Response): Promise<T> {
  if (!r.ok) {
    const body = await r.json().catch(() => ({}));
    throw new Error((body as { detail?: string }).detail ?? `HTTP ${r.status}`);
  }
  return r.json() as Promise<T>;
}

export const chargerCorrespondances = (produitId?: number): Promise<Cluster[]> =>
  fetch(`/api/correspondances${produitId ? `?produit_id=${produitId}` : ''}`).then(
    (r) => json<Cluster[]>(r)
  );

export const analyserCorrespondances = (produitId?: number): Promise<Cluster[]> =>
  fetch(
    `/api/correspondances/analyser${produitId ? `?produit_id=${produitId}` : ''}`,
    { method: 'POST' }
  ).then((r) => json<Cluster[]>(r));
