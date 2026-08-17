export type Vue =
  | { nom: 'sources:entretiens' }
  | { nom: 'sources:entretiens:ajout' }
  | { nom: 'sources:entretiens:detail'; id: number }
  | { nom: 'sources:entretiens:modification'; id: number }
  | { nom: 'sources:retours-bizdev' }
  | { nom: 'sources:featurebase' }
  | { nom: 'analyses' }
  | { nom: 'besoins' }
  | { nom: 'correspondances' };

export type SourceBesoin = 'transcript' | 'retour_bizdev' | 'idee';

export type Membre = {
  source: string;
  texte: string;
  transcript_id: number | null;
  verbatim: string | null;
};

export type Cluster = {
  libelle: string;
  occurrences: number;
  membres: Membre[];
};

export type Idee = {
  id: number;
  titre: string;
  nb_votes: number;
  importe_le: string;
};

export type RetourBizDev = {
  id: number;
  verbatim: string;
  categorie: string | null;
  item: string | null;
  role: string | null;
  qui: string | null;
  date_retour: string | null;
  importe_le: string;
};

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
  verbatim: string | null;
  cree_le: string;
};
