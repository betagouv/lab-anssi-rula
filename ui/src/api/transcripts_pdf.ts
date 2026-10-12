import { requete } from './requete';

export type AnalyseTranscriptPdf = { contenu: Record<string, unknown> };
export type SourceTranscriptPdf = {
  type_source: 'produit' | 'bizdev';
  produit_id: number;
  projet_id: number | null;
};

export const obtenirSourceTranscriptPdf = (transcriptId: number) =>
  requete<SourceTranscriptPdf>(`/api/transcripts-pdf/${transcriptId}`);

export const obtenirAnalyseTranscriptPdf = (transcriptId: number) =>
  requete<AnalyseTranscriptPdf | null>(
    `/api/transcripts-pdf/${transcriptId}/analyse`
  );
