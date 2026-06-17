export type Vue =
  | { nom: 'transcripts:liste' }
  | { nom: 'transcripts:ajout' }
  | { nom: 'transcripts:detail'; id: number }
  | { nom: 'transcripts:modification'; id: number }
  | { nom: 'analyses' };

export type Transcript = {
  id: number;
  identite_id: number;
  produit_id: number;
  date_entretien: string;
  contenu: string;
  cree_le: string;
  modifie_le: string;
};

export type Analyse = {
  id: number;
  transcript_id: number;
  contenu: string;
  cree_le: string;
};

export type Fonctionnalite = {
  id: number;
  transcript_id: number;
  contenu: string;
  cree_le: string;
};
