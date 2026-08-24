import type { RetourBizDev } from '../types';
import { json } from './requete';

export const importerRetours = (fichier: File): Promise<RetourBizDev[]> => {
  const form = new FormData();
  form.append('fichier', fichier);
  return fetch('/api/retours-bizdev/import', { method: 'POST', body: form }).then(
    (r) => json<RetourBizDev[]>(r)
  );
};

export const listerRetours = (): Promise<RetourBizDev[]> =>
  fetch('/api/retours-bizdev').then((r) => json<RetourBizDev[]>(r));
