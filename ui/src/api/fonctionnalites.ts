import type { Fonctionnalite } from '../types';

async function json<T>(r: Response): Promise<T> {
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  return r.json() as Promise<T>;
}

export const obtenirFonctionnalites = (
  transcript_id: number
): Promise<Fonctionnalite[] | null> =>
  fetch(`/api/fonctionnalites/transcripts/${transcript_id}`).then((r) => {
    if (r.status === 404) return null;
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    return r.json() as Promise<Fonctionnalite[]>;
  });

export const calculerFonctionnalites = (
  transcript_id: number
): Promise<Fonctionnalite[]> =>
  fetch(`/api/fonctionnalites/transcripts/${transcript_id}`, {
    method: 'POST',
  }).then((r) => json<Fonctionnalite[]>(r));

export const listerFonctionnalites = (): Promise<Fonctionnalite[]> =>
  fetch('/api/fonctionnalites').then((r) => json<Fonctionnalite[]>(r));
