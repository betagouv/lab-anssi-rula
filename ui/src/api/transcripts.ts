import type { Transcript } from '../types';
import { ErreurApi, requete } from './requete';

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

async function corps<T>(url: string, init?: RequestInit): Promise<T> {
  try {
    return await requete<T>(url, init);
  } catch (erreur) {
    if (erreur instanceof ErreurApi && erreur.statut === 422) {
      const detail = erreur.detail;
      if (
        typeof detail === 'object' &&
        detail !== null &&
        'raisons' in detail &&
        Array.isArray(detail.raisons) &&
        detail.raisons.every(estRaisonRefusTranscript)
      )
        throw new TranscriptNonConforme(detail.raisons);
    }
    throw erreur;
  }
}

export const listerTranscripts = () => requete<Transcript[]>('/api/transcripts');

export const obtenirTranscript = (id: number) =>
  requete<Transcript>(`/api/transcripts/${id}`);

export const ajouterTranscript = (body: NouveauTranscript) =>
  corps<Transcript>('/api/transcripts', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });

export const modifierTranscript = (id: number, body: NouveauTranscript) =>
  corps<Transcript>(`/api/transcripts/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });

export const supprimerTranscript = (id: number) =>
  requete<void>(`/api/transcripts/${id}`, { method: 'DELETE' });
