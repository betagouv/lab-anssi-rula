import type { SourceBesoin } from '../types';

export type BesoinDetecte = {
  id: number;
  source: SourceBesoin;
  source_id: number;
  texte_original: string;
  nom_generique: string;
  verbatim: string | null;
  transcript_id: number | null;
  statut: string;
  cree_le: string;
};

async function json<T>(r: Response): Promise<T> {
  if (!r.ok) {
    const body = await r.json().catch(() => ({}));
    throw new Error((body as { detail?: string }).detail ?? `HTTP ${r.status}`);
  }
  return r.json() as Promise<T>;
}

export const listerBesoins = (source: SourceBesoin): Promise<BesoinDetecte[]> =>
  fetch(`/api/besoins?source=${encodeURIComponent(source)}`).then((r) =>
    json<BesoinDetecte[]>(r)
  );

export const analyserBesoins = (source: SourceBesoin): Promise<BesoinDetecte[]> =>
  fetch(`/api/besoins/analyser/${source}`, { method: 'POST' }).then((r) =>
    json<BesoinDetecte[]>(r)
  );
