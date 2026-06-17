import type { Idee } from '../types';

async function json<T>(r: Response): Promise<T> {
  if (!r.ok) {
    const body = await r.json().catch(() => ({}));
    throw new Error((body as { detail?: string }).detail ?? `HTTP ${r.status}`);
  }
  return r.json() as Promise<T>;
}

export const importerIdees = (fichier: File): Promise<Idee[]> => {
  const form = new FormData();
  form.append('fichier', fichier);
  return fetch('/api/idees/import', { method: 'POST', body: form }).then((r) =>
    json<Idee[]>(r)
  );
};

export const listerIdees = (): Promise<Idee[]> =>
  fetch('/api/idees').then((r) => json<Idee[]>(r));
