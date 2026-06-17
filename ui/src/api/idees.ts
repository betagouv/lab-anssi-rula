import type { Idee } from '../types';

async function json<T>(r: Response): Promise<T> {
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  return r.json() as Promise<T>;
}

export const synchroniserIdees = (): Promise<Idee[]> =>
  fetch('/api/idees/sync', { method: 'POST' }).then((r) => json<Idee[]>(r));

export const listerIdees = (): Promise<Idee[]> =>
  fetch('/api/idees').then((r) => json<Idee[]>(r));
