import { requete } from './requete';

export const envoyerCsv = <T>(
  endpoint: string,
  fichier: File,
  champs: Record<string, string>
): Promise<T> => {
  const form = new FormData();
  form.append('fichier', fichier);
  for (const [nom, valeur] of Object.entries(champs)) form.append(nom, valeur);
  return requete<T>(endpoint, { method: 'POST', body: form });
};

export const champsSelection = (selection: {
  projet_id?: number;
  nouveau_projet?: { nom: string; brief: string };
}): Record<string, string> => ({
  ...(selection.projet_id ? { projet_id: String(selection.projet_id) } : {}),
  ...(selection.nouveau_projet
    ? {
        nouveau_projet_nom: selection.nouveau_projet.nom,
        nouveau_projet_brief: selection.nouveau_projet.brief,
      }
    : {}),
});
