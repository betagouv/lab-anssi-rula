import type { RetourBizDev } from '../types';
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
  form.append('confirmation', 'true');
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
  selection: { projet_id?: number; nouveau_projet?: { nom: string; brief: string } },
  confirmation: boolean
) => {
  const form = new FormData();
  form.append('fichier', fichier);
  form.append('confirmation', String(confirmation));
  if (selection.projet_id) form.append('projet_id', String(selection.projet_id));
  if (selection.nouveau_projet) {
    form.append('nouveau_projet_nom', selection.nouveau_projet.nom);
    form.append('nouveau_projet_brief', selection.nouveau_projet.brief);
  }
  return fetch(`/api/produits/${produitId}/sources/bizdev`, {
    method: 'POST',
    body: form,
  }).then((r) =>
    json<{ projet: { id: number; nom: string }; sources: RetourBizDev[] }>(r)
  );
};

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
