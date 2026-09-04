import type { Fonctionnalite } from '../types';
import { ErreurApi, requete } from './requete';

export const obtenirFonctionnalites = (
  transcript_id: number
): Promise<Fonctionnalite[] | null> =>
  requete<Fonctionnalite[]>(
    `/api/fonctionnalites/transcripts/${transcript_id}`
  ).catch((erreur) => {
    if (erreur instanceof ErreurApi && erreur.statut === 404) return null;
    throw erreur;
  });

export const calculerFonctionnalites = (
  transcript_id: number
): Promise<Fonctionnalite[]> =>
  requete<Fonctionnalite[]>(`/api/fonctionnalites/transcripts/${transcript_id}`, {
    method: 'POST',
  });

export const listerFonctionnalites = (): Promise<Fonctionnalite[]> =>
  requete<Fonctionnalite[]>('/api/fonctionnalites');
