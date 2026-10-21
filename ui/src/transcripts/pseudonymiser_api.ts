import { requete } from '../api/requete';

export type Produit = { id: number; nom: string };
export type TranscriptPdf = {
  id: number;
  type_source: 'produit' | 'bizdev';
  produit_id: number;
  nom_source: string;
  date_entretien: string | null;
  contenu: string;
  contexte: string;
  locuteurs: { identifiant: string; role: string; nom_affiche: string }[];
  cree_le: string;
};

export const nomPseudonymise = (nom: string) =>
  `pseudonymiser_${nom.replace(/^(?:pseudonymiser_)+/i, '')}`;

export const listerProduits = () => requete<Produit[]>('/api/produits');
export const listerTranscriptsPdf = (produitId: number) =>
  requete<TranscriptPdf[]>(`/api/transcripts-pdf/produits/${produitId}`);
export const obtenirTranscriptPdf = (id: number) =>
  requete<TranscriptPdf>(`/api/transcripts-pdf/${id}`);
export const supprimerTranscriptPdf = (id: number) =>
  requete<void>(`/api/transcripts-pdf/${id}`, { method: 'DELETE' });
