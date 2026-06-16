import type { Transcript } from '../types';

export type NouveauTranscript = {
  identite_id: number;
  produit_id: number;
  date_entretien: string;
  contenu: string;
};

async function json<T>(r: Response): Promise<T> {
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  return r.json() as Promise<T>;
}

export const listerTranscripts = () =>
  fetch('/api/transcripts').then((r) => json<Transcript[]>(r));

export const obtenirTranscript = (id: number) =>
  fetch(`/api/transcripts/${id}`).then((r) => json<Transcript>(r));

export const ajouterTranscript = (body: NouveauTranscript) =>
  fetch('/api/transcripts', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  }).then((r) => json<Transcript>(r));

export const modifierTranscript = (id: number, body: NouveauTranscript) =>
  fetch(`/api/transcripts/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  }).then((r) => json<Transcript>(r));

export const supprimerTranscript = (id: number) =>
  fetch(`/api/transcripts/${id}`, { method: 'DELETE' }).then((r) => {
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
  });
