import type { Cluster, SourceBesoin } from '../types';
import { requete } from './requete';

export type Besoin = {
  id: number;
  source: SourceBesoin;
  source_id: number;
  texte_original: string;
  nom_generique: string;
  verbatim: string | null;
  transcript_id: number | null;
  projet_id: number | null;
  statut: string;
  cree_le: string;
  produit_id: number | null;
};

export type AnalyseTransverse = {
  besoins: Besoin[];
  correspondances: Cluster[];
  groupes: GroupeTransverse[];
  calcule_le: string | null;
};

export type PassageTransverse = {
  source: 'transcript' | 'idee' | 'retour_bizdev';
  source_id: number | null;
  transcript_id: number | null;
  projet_id: number | null;
  texte_normalise: string;
  verbatim: string;
};

export type GroupeTransverse = {
  nom_generique: string;
  occurrences: number;
  passages: PassageTransverse[];
};

export const obtenirAnalyseTransverse = (
  produitId: number
): Promise<AnalyseTransverse> =>
  requete<AnalyseTransverse>(`/api/produits/${produitId}/analyse-transverse`);

export const analyserTransverse = (produitId: number): Promise<AnalyseTransverse> =>
  requete<AnalyseTransverse>(`/api/produits/${produitId}/analyse-transverse`, {
    method: 'POST',
  });
