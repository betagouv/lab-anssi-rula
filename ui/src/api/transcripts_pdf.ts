import { requete } from './requete';

export type AnalyseTranscriptPdf = { contenu: Record<string, unknown> };

export const obtenirAnalyseTranscriptPdf = (transcriptId: number) =>
  requete<AnalyseTranscriptPdf | null>(
    `/api/transcripts-pdf/${transcriptId}/analyse`
  );
