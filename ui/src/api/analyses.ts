import type { Analyse } from '../types';

async function json<T>(r: Response): Promise<T> {
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  return r.json() as Promise<T>;
}

export const obtenirAnalyse = (transcript_id: number): Promise<Analyse | null> =>
  fetch(`/api/analyses/transcripts/${transcript_id}`).then((r) => {
    if (r.status === 404) return null;
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    return r.json() as Promise<Analyse>;
  });

export const genererAnalyse = (transcript_id: number): Promise<Analyse> =>
  fetch(`/api/analyses/transcripts/${transcript_id}`, { method: 'POST' }).then((r) =>
    json<Analyse>(r)
  );

export const listerAnalyses = (): Promise<Analyse[]> =>
  fetch('/api/analyses').then((r) => json<Analyse[]>(r));
