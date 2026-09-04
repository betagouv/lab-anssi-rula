import type { Idee } from '../types';
import { champsSelection, envoyerCsv } from './import_csv';
import { requete } from './requete';

export const importerIdees = (fichier: File, produitId: number): Promise<Idee[]> => {
  const form = new FormData();
  form.append('fichier', fichier);
  form.append('produit_id', String(produitId));
  return requete<Idee[]>('/api/idees/import', { method: 'POST', body: form });
};

export const importerIdeesProjet = (
  fichier: File,
  produitId: number,
  selection: { projet_id?: number; nouveau_projet?: { nom: string; brief: string } }
) => {
  return envoyerCsv<{ projet: { id: number; nom: string }; sources: Idee[] }>(
    `/api/produits/${produitId}/sources/featurebase`,
    fichier,
    champsSelection(selection)
  );
};

export const importerIdeesProduit = (fichier: File, produitId: number) =>
  envoyerCsv<{ produit_id: number; sources: Idee[] }>(
    `/api/produits/${produitId}/sources/featurebase`,
    fichier,
    {}
  );

export const listerIdees = (
  produitId?: number,
  projetId?: number
): Promise<Idee[]> =>
  requete<Idee[]>(
    `/api/idees?${new URLSearchParams({
      ...(produitId ? { produit_id: String(produitId) } : {}),
      ...(projetId ? { projet_id: String(projetId) } : {}),
    })}`
  );
