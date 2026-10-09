import type { ProgressionPreparation } from './progression';

type LocuteurPreparation = {
  identifiant: string;
  role: 'interne' | 'externe' | 'indetermine';
  justification: string;
};

type RemplacementPreparation = {
  valeur_originale: string;
  valeur_anonyme: string;
  categorie: string;
  champ: string;
};

export type ResultatPreparation =
  | { statut: 'en_cours'; progression: ProgressionPreparation }
  | { statut: 'echec'; progression: ProgressionPreparation; erreur: string }
  | {
      statut: 'termine';
      progression: ProgressionPreparation;
      nom_source: string;
      date_entretien: string | null;
      contenu: string;
      contexte: string;
      locuteurs: LocuteurPreparation[];
      remplacements: RemplacementPreparation[];
    };

export class ErreurSuiviPreparation extends Error {
  constructor(readonly code: 'introuvable' | 'indisponible') {
    super(code);
  }
}

export async function lirePreparation(
  jeton: string,
  get: (url: string, signal: AbortSignal) => Promise<Response>,
  signalExterne?: AbortSignal,
  delai = 10_000
): Promise<ResultatPreparation> {
  const controle = new AbortController();
  const annuler = () => controle.abort();
  signalExterne?.addEventListener('abort', annuler, { once: true });
  if (signalExterne?.aborted) controle.abort();
  const timer = setTimeout(() => controle.abort(), delai);
  try {
    const reponse = await get(
      `/api/transcripts-pdf/preparation/${encodeURIComponent(jeton)}`,
      controle.signal
    );
    if (reponse.status === 404) throw new ErreurSuiviPreparation('introuvable');
    if (!reponse.ok) throw new ErreurSuiviPreparation('indisponible');
    return (await reponse.json()) as ResultatPreparation;
  } finally {
    clearTimeout(timer);
    signalExterne?.removeEventListener('abort', annuler);
  }
}
