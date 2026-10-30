import { requete } from '../api/requete';

export type Produit = { id: number; nom: string };
export type CouleurListe = 'blanche' | 'noire';
export type TermeListe = { id: number; terme: string; revision: number };
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
export const listerTermes = (couleur: CouleurListe) =>
  requete<TermeListe[]>(`/api/liste-${couleur}`);
export const ajouterTerme = (couleur: CouleurListe, terme: string) =>
  requete<TermeListe>(`/api/liste-${couleur}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ terme }),
  });
export const modifierTerme = (
  couleur: CouleurListe,
  id: number,
  terme: string,
  revision: number
) =>
  requete<TermeListe>(`/api/liste-${couleur}/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ terme, revision }),
  });
export const supprimerTerme = (
  couleur: CouleurListe,
  id: number,
  revision: number
) =>
  requete<void>(`/api/liste-${couleur}/${id}?revision=${revision}`, {
    method: 'DELETE',
  });
export const listerTranscriptsPdf = (produitId: number) =>
  requete<TranscriptPdf[]>(`/api/transcripts-pdf/produits/${produitId}`);
export const obtenirTranscriptPdf = (id: number) =>
  requete<TranscriptPdf>(`/api/transcripts-pdf/${id}`);
export const supprimerTranscriptPdf = (id: number) =>
  requete<void>(`/api/transcripts-pdf/${id}`, { method: 'DELETE' });
