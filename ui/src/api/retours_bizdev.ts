import type { RetourBizDev } from '../types';
import { champsSelection, envoyerCsv } from './import_csv';
import { json } from './requete';

export const importerRetours = (
  fichier: File,
  produitId: number,
  selection: {
    projet_id?: number;
    nouveau_projet?: { nom: string; brief: string };
  } = {}
): Promise<RetourBizDev[]> => {
  const form = new FormData();
  form.append('fichier', fichier);
  form.append('produit_id', String(produitId));
  if (selection.projet_id) form.append('projet_id', String(selection.projet_id));
  if (selection.nouveau_projet) {
    form.append('nouveau_projet_nom', selection.nouveau_projet.nom);
    form.append('nouveau_projet_brief', selection.nouveau_projet.brief);
  }
  return fetch('/api/retours-bizdev/import', { method: 'POST', body: form }).then(
    (r) => json<RetourBizDev[]>(r)
  );
};

export const importerRetoursProjet = (
  fichier: File,
  produitId: number,
  selection: { projet_id?: number; nouveau_projet?: { nom: string; brief: string } }
) => {
  return envoyerCsv<{
    projet: { id: number; nom: string };
    sources: RetourBizDev[];
  }>(
    `/api/produits/${produitId}/sources/bizdev`,
    fichier,
    champsSelection(selection)
  );
};

export const importerRetoursProduit = (fichier: File, produitId: number) =>
  envoyerCsv<{ produit_id: number; sources: RetourBizDev[] }>(
    `/api/produits/${produitId}/sources/bizdev`,
    fichier,
    {}
  );

export const listerRetours = (
  produitId?: number,
  projetId?: number
): Promise<RetourBizDev[]> =>
  fetch(
    `/api/retours-bizdev?${new URLSearchParams({
      ...(produitId ? { produit_id: String(produitId) } : {}),
      ...(projetId ? { projet_id: String(projetId) } : {}),
    })}`
  ).then((r) => json<RetourBizDev[]>(r));
