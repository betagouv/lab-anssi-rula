import type { Idee } from '../types';
import { champsSelection, envoyerCsv } from './import_csv';
import { json } from './requete';

export const importerIdees = (fichier: File, produitId: number): Promise<Idee[]> => {
  const form = new FormData();
  form.append('fichier', fichier);
  form.append('produit_id', String(produitId));
  return fetch('/api/idees/import', { method: 'POST', body: form }).then((r) =>
    json<Idee[]>(r)
  );
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
  fetch(
    `/api/idees?${new URLSearchParams({
      ...(produitId ? { produit_id: String(produitId) } : {}),
      ...(projetId ? { projet_id: String(projetId) } : {}),
    })}`
  ).then((r) => json<Idee[]>(r));
