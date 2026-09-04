import type { Analyse } from '../types';
import { ErreurApi, requete } from './requete';

export const obtenirAnalyse = (transcript_id: number): Promise<Analyse | null> =>
  requete<Analyse>(`/api/analyses/transcripts/${transcript_id}`).catch((erreur) => {
    if (erreur instanceof ErreurApi && erreur.statut === 404) return null;
    throw erreur;
  });

export const genererAnalyse = (transcript_id: number): Promise<Analyse> =>
  requete<Analyse>(`/api/analyses/transcripts/${transcript_id}`, { method: 'POST' });

export const listerAnalyses = (): Promise<Analyse[]> =>
  requete<Analyse[]>('/api/analyses');
