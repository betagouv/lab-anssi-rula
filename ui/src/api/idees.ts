import type { Idee } from '../types';
import { json } from './requete';

export const importerIdees = (fichier: File, produitId: number): Promise<Idee[]> => {
  const form = new FormData();
  form.append('fichier', fichier);
  form.append('produit_id', String(produitId));
  form.append('confirmation', 'true');
  return fetch('/api/idees/import', { method: 'POST', body: form }).then((r) =>
    json<Idee[]>(r)
  );
};

export const importerIdeesProjet = (
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
  return fetch(`/api/produits/${produitId}/sources/featurebase`, {
    method: 'POST',
    body: form,
  }).then((r) => json<{ projet: { id: number; nom: string }; sources: Idee[] }>(r));
};

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
