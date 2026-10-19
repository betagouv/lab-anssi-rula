import { requete } from './requete';

export type TranscriptCatalogueClaude = {
  id: number;
  produit_id: number;
  revision: number;
  nombre_rapports: number;
  analyse_courante: boolean;
};

export type RapportClaude = {
  id: number;
  transcript_id: number;
  cree_le: string;
  courant: boolean;
  contenu: string;
};

export async function listerTranscriptsClaude(
  produitId: number,
  typeSource: string
): Promise<{ elements: TranscriptCatalogueClaude[] }> {
  const elements: TranscriptCatalogueClaude[] = [];
  let curseur: number | null = null;
  do {
    const parametres = new URLSearchParams({
      produit_id: String(produitId),
      type_source: typeSource,
      limite: '100',
    });
    if (curseur !== null) parametres.set('curseur', String(curseur));
    const page = await requete<{
      elements: TranscriptCatalogueClaude[];
      curseur_suivant: number | null;
    }>(`/api/rapports-claude/transcripts?${parametres}`);
    elements.push(...page.elements);
    curseur = page.curseur_suivant;
  } while (curseur !== null);
  return { elements };
}

export async function listerRapportsClaude(
  transcriptId: number
): Promise<{ elements: { id: number; cree_le: string; courant: boolean }[] }> {
  const elements: { id: number; cree_le: string; courant: boolean }[] = [];
  let curseur: number | null = null;
  do {
    const parametres = new URLSearchParams({ limite: '100' });
    if (curseur !== null) parametres.set('curseur', String(curseur));
    const page = await requete<{
      elements: { id: number; cree_le: string; courant: boolean }[];
      curseur_suivant: number | null;
    }>(`/api/rapports-claude/transcripts/${transcriptId}/rapports?${parametres}`);
    elements.push(...page.elements);
    curseur = page.curseur_suivant;
  } while (curseur !== null);
  return { elements };
}

export async function lireRapportClaude(rapportId: number): Promise<RapportClaude> {
  let contenu = '';
  let offset = 0;
  let date = '';
  let courant = false;
  let transcriptId = 0;
  do {
    const bloc = await requete<{
      bloc: string;
      transcript_id: number;
      offset_suivant: number | null;
      cree_le: string;
      courant: boolean;
    }>(`/api/rapports-claude/${rapportId}?offset=${offset}`);
    contenu += bloc.bloc;
    date = bloc.cree_le;
    courant = bloc.courant;
    transcriptId = bloc.transcript_id;
    offset = bloc.offset_suivant ?? -1;
  } while (offset !== -1);
  return {
    id: rapportId,
    transcript_id: transcriptId,
    cree_le: date,
    courant,
    contenu,
  };
}
