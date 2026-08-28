import { json } from './requete';

export type RaisonRefusProjet = {
  categorie: string;
  element: string;
  raison: string;
};

export class ProjetNonConforme extends Error {
  constructor(readonly raisons: RaisonRefusProjet[]) {
    super("Le projet n'a pas été enregistré.");
  }
}

function estRaisonRefus(raison: unknown): raison is RaisonRefusProjet {
  return (
    typeof raison === 'object' &&
    raison !== null &&
    'categorie' in raison &&
    typeof raison.categorie === 'string' &&
    'element' in raison &&
    typeof raison.element === 'string' &&
    'raison' in raison &&
    typeof raison.raison === 'string'
  );
}

export type Produit = { id: number; nom: string };
export type Projet = {
  id: number;
  produit_id: number;
  nom: string;
  brief: string;
  cree_le: string;
};
export type Entretien = {
  id: number;
  projet_id: number;
  participant: string;
  date_entretien: string;
  moderateur: string;
  contenu: string;
  note_moderateur: string;
  cree_le: string;
};
export type Scan = {
  projet_id: number;
  brouillon: string;
  valide: string | null;
  cree_le: string;
  modifie_le: string;
};

export type BlocPrompt = {
  cle: string;
  libelle: string;
  contenu: string;
  ordre: number;
};

export type EtapeAnalyse = {
  projet_id: number;
  cle: string;
  libelle: string;
  ordre: number;
  prompt: string;
  brouillon: string | null;
  valide: string | null;
  cree_le: string;
  modifie_le: string;
};

export type ConfigurationAnalyse = {
  blocs: BlocPrompt[];
  etapes: EtapeAnalyse[];
};

export type SourceProjet = { projet: Projet; entretien: Entretien };

const corps = async <T>(url: string, body: unknown, method = 'POST'): Promise<T> => {
  const reponse = await fetch(url, {
    method,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  const contenu = (await reponse.json()) as { detail?: unknown };
  if (
    reponse.status === 422 &&
    typeof contenu.detail === 'object' &&
    contenu.detail !== null &&
    'raisons' in contenu.detail &&
    Array.isArray(contenu.detail.raisons) &&
    contenu.detail.raisons.every(estRaisonRefus)
  )
    throw new ProjetNonConforme(contenu.detail.raisons);
  if (!reponse.ok)
    throw new Error(
      typeof contenu.detail === 'string' ? contenu.detail : `HTTP ${reponse.status}`
    );
  return contenu as T;
};

export const listerProduits = () => fetch('/api/produits').then(json<Produit[]>);
export const listerProjets = (produitId: number) =>
  fetch(`/api/projets?produit_id=${produitId}`).then(json<Projet[]>);
export const obtenirProjet = (id: number) =>
  fetch(`/api/projets/${id}`).then(json<Projet>);
export const creerProjet = (body: {
  produit_id: number;
  nom: string;
  brief: string;
}) => corps<Projet>('/api/projets', body);
export const ajouterSource = (
  produitId: number,
  body: {
    projet_id?: number;
    nouveau_projet?: { nom: string; brief: string };
    entretien: Omit<Entretien, 'id' | 'projet_id' | 'cree_le'>;
    confirmation: boolean;
  }
) => corps<SourceProjet>(`/api/produits/${produitId}/sources`, body);
export const listerEntretiens = (id: number) =>
  fetch(`/api/projets/${id}/entretiens`).then(json<Entretien[]>);
export const creerEntretien = (
  id: number,
  body: Omit<Entretien, 'id' | 'projet_id' | 'cree_le'> & { confirmation: boolean }
) => corps<Entretien>(`/api/projets/${id}/entretiens`, body);
export const obtenirScan = (id: number) =>
  fetch(`/api/projets/${id}/scan`).then(json<Scan>);
export const genererScan = (id: number) =>
  corps<Scan>(`/api/projets/${id}/scan`, {});
export const modifierScan = (id: number, contenu: string) =>
  corps<Scan>(`/api/projets/${id}/scan`, { contenu }, 'PUT');
export const validerScan = (id: number) =>
  corps<Scan>(`/api/projets/${id}/scan/validation`, {});
export const obtenirConfigurationAnalyse = (id: number) =>
  fetch(`/api/projets/${id}/analyse/configuration`).then(json<ConfigurationAnalyse>);
export const modifierConfigurationAnalyse = (
  id: number,
  blocs: Record<string, string>
) =>
  corps<ConfigurationAnalyse>(
    `/api/projets/${id}/analyse/configuration`,
    { blocs },
    'PUT'
  );
export const genererEtapeAnalyse = (id: number, cle: string) =>
  corps<EtapeAnalyse>(`/api/projets/${id}/analyse/etapes/${cle}/generation`, {});
export const modifierEtapeAnalyse = (id: number, cle: string, contenu: string) =>
  corps<EtapeAnalyse>(
    `/api/projets/${id}/analyse/etapes/${cle}`,
    { contenu },
    'PUT'
  );
export const validerEtapeAnalyse = (id: number, cle: string) =>
  corps<EtapeAnalyse>(`/api/projets/${id}/analyse/etapes/${cle}/validation`, {});
export const obtenirDetailAnalyse = (id: number) =>
  fetch(`/api/projets/${id}/analyse/detail`).then(
    json<{ etapes: { cle: string; libelle: string; contenu: string }[] }>
  );
