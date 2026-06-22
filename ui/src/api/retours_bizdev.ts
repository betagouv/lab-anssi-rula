import type { RetourBizDev } from '../types';

async function json<T>(r: Response): Promise<T> {
  if (!r.ok) {
    const body = await r.json().catch(() => ({}));
    throw new Error((body as { detail?: string }).detail ?? `HTTP ${r.status}`);
  }
  return r.json() as Promise<T>;
}

export const importerRetours = (fichier: File): Promise<RetourBizDev[]> => {
  const form = new FormData();
  form.append('fichier', fichier);
  return fetch('/api/retours-bizdev/import', { method: 'POST', body: form }).then(
    (r) => json<RetourBizDev[]>(r)
  );
};

export const listerRetours = (): Promise<RetourBizDev[]> =>
  fetch('/api/retours-bizdev').then((r) => json<RetourBizDev[]>(r));
