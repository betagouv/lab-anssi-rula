import type { Idee } from '../types';
import { json } from './requete';

export const importerIdees = (fichier: File): Promise<Idee[]> => {
  const form = new FormData();
  form.append('fichier', fichier);
  return fetch('/api/idees/import', { method: 'POST', body: form }).then((r) =>
    json<Idee[]>(r)
  );
};

export const listerIdees = (): Promise<Idee[]> =>
  fetch('/api/idees').then((r) => json<Idee[]>(r));
