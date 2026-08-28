import type { RetourBizDev } from '../types';
import { json } from './requete';

export const importerRetours = (
  fichier: File,
  produitId: number
): Promise<RetourBizDev[]> => {
  const form = new FormData();
  form.append('fichier', fichier);
  form.append('produit_id', String(produitId));
  form.append('confirmation', 'true');
  return fetch('/api/retours-bizdev/import', { method: 'POST', body: form }).then(
    (r) => json<RetourBizDev[]>(r)
  );
};

export const listerRetours = (produitId?: number): Promise<RetourBizDev[]> =>
  fetch(`/api/retours-bizdev${produitId ? `?produit_id=${produitId}` : ''}`).then(
    (r) => json<RetourBizDev[]>(r)
  );
