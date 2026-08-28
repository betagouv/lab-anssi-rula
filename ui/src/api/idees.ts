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

export const listerIdees = (produitId?: number): Promise<Idee[]> =>
  fetch(`/api/idees${produitId ? `?produit_id=${produitId}` : ''}`).then((r) =>
    json<Idee[]>(r)
  );
