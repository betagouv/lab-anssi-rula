import { ErreurApi, requete } from './requete';

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
  statut: string;
  cree_le: string;
  modifie_le: string;
};

export type ConfigurationAnalyse = {
  blocs: BlocPrompt[];
  etapes: EtapeAnalyse[];
};

export type SourceProjet = { projet: Projet; entretien: Entretien };

const corps = async <T>(url: string, body: unknown, method = 'POST'): Promise<T> => {
  try {
    return await requete<T>(url, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
  } catch (erreur) {
    if (erreur instanceof ErreurApi && erreur.statut === 422) {
      const detail = erreur.detail;
      if (
        typeof detail === 'object' &&
        detail !== null &&
        'raisons' in detail &&
        Array.isArray(detail.raisons) &&
        detail.raisons.every(estRaisonRefus)
      )
        throw new ProjetNonConforme(detail.raisons);
    }
    throw erreur;
  }
};

export const listerProduits = () => requete<Produit[]>('/api/produits');
export const listerProjets = (produitId: number) =>
  requete<Projet[]>(`/api/projets?produit_id=${produitId}`);
export const obtenirProjet = (id: number) => requete<Projet>(`/api/projets/${id}`);
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
  requete<Entretien[]>(`/api/projets/${id}/entretiens`);
export const obtenirEntretien = (projetId: number, entretienId: number) =>
  requete<Entretien>(`/api/projets/${projetId}/entretiens/${entretienId}`);
export const creerEntretien = (
  id: number,
  body: Omit<Entretien, 'id' | 'projet_id' | 'cree_le'> & { confirmation: boolean }
) => corps<Entretien>(`/api/projets/${id}/entretiens`, body);
export const obtenirScan = (id: number) => requete<Scan>(`/api/projets/${id}/scan`);
export const genererScan = (id: number) =>
  corps<Scan>(`/api/projets/${id}/scan`, {});
export const modifierScan = (id: number, contenu: string) =>
  corps<Scan>(`/api/projets/${id}/scan`, { contenu }, 'PUT');
export const validerScan = (id: number) =>
  corps<Scan>(`/api/projets/${id}/scan/validation`, {});
export const obtenirConfigurationAnalyse = (id: number) =>
  requete<ConfigurationAnalyse>(`/api/projets/${id}/analyse/configuration`);
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
  requete<{ etapes: { cle: string; libelle: string; contenu: string }[] }>(
    `/api/projets/${id}/analyse/detail`
  );
