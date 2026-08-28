import type { Cluster, SourceBesoin } from '../types';
import { json } from './requete';

export type Besoin = {
  id: number;
  source: SourceBesoin;
  source_id: number;
  texte_original: string;
  nom_generique: string;
  verbatim: string | null;
  transcript_id: number | null;
  statut: string;
  cree_le: string;
  produit_id: number | null;
};

export type AnalyseTransverse = {
  besoins: Besoin[];
  correspondances: Cluster[];
  calcule_le: string | null;
};

export const obtenirAnalyseTransverse = (
  produitId: number
): Promise<AnalyseTransverse> =>
  fetch(`/api/produits/${produitId}/analyse-transverse`).then((r) =>
    json<AnalyseTransverse>(r)
  );

export const analyserTransverse = (produitId: number): Promise<AnalyseTransverse> =>
  fetch(`/api/produits/${produitId}/analyse-transverse`, { method: 'POST' }).then(
    (r) => json<AnalyseTransverse>(r)
  );
