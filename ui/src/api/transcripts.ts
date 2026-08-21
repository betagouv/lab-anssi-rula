import type { Transcript } from '../types';

export type NouveauTranscript = {
  identite_id?: number;
  nouvelle_identite?: string;
  produit_id?: number;
  nouveau_produit?: string;
  date_entretien: string;
  contenu: string;
};

export type RaisonRefusTranscript = {
  categorie: string;
  element: string;
  raison: string;
};

export class TranscriptNonConforme extends Error {
  constructor(readonly raisons: RaisonRefusTranscript[]) {
    super("Le transcript n'a pas été enregistré.");
  }
}

function estRaisonRefusTranscript(raison: unknown): raison is RaisonRefusTranscript {
  return (
    typeof raison === 'object' &&
    raison !== null &&
    'categorie' in raison &&
    typeof raison.categorie === 'string' &&
    'element' in raison &&
    typeof raison.element === 'string' &&
    'raison' in raison &&
    typeof raison.raison === 'string'
  );
}

async function json<T>(r: Response): Promise<T> {
  const body = (await r.json()) as { detail?: unknown };
  if (
    r.status === 422 &&
    typeof body.detail === 'object' &&
    body.detail !== null &&
    'raisons' in body.detail &&
    Array.isArray(body.detail.raisons) &&
    body.detail.raisons.every(estRaisonRefusTranscript)
  ) {
    throw new TranscriptNonConforme(body.detail.raisons);
  }
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  return body as T;
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
