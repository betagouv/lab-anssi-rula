type Objet = Record<string, unknown>;

function estObjet(valeur: unknown): valeur is Objet {
  return typeof valeur === 'object' && valeur !== null;
}

function messagesChamps(champs: unknown): string[] {
  if (!Array.isArray(champs)) return [];
  return champs.flatMap((champ) => {
    if (typeof champ === 'string') return [champ];
    if (estObjet(champ) && typeof champ.message === 'string') return [champ.message];
    return [];
  });
}

export function messageDetail(detail: unknown, statut: number): string {
  if (typeof detail === 'string' && detail.trim()) return detail;
  if (estObjet(detail)) {
    const message = typeof detail.message === 'string' ? detail.message : '';
    const champs = messagesChamps(detail.champs);
    if (message || champs.length)
      return [message, ...champs].filter(Boolean).join(' ');
    if (Array.isArray(detail.raisons))
      return 'Les données saisies ne peuvent pas être enregistrées.';
  }
  return `Le serveur a renvoyé une réponse invalide (HTTP ${statut}).`;
}

export class ErreurApi extends Error {
  constructor(
    readonly statut: number,
    readonly detail: unknown,
    message = messageDetail(detail, statut)
  ) {
    super(message);
    this.name = 'ErreurApi';
  }
}

export async function json<T>(reponse: Response): Promise<T> {
  if (reponse.status === 204) return undefined as T;
  let contenu: unknown;
  try {
    contenu = await reponse.json();
  } catch {
    throw new ErreurApi(
      reponse.status,
      undefined,
      reponse.ok
        ? 'La réponse du serveur est invalide. Réessayez.'
        : `Le serveur a renvoyé une réponse invalide (HTTP ${reponse.status}).`
    );
  }
  if (!reponse.ok)
    throw new ErreurApi(
      reponse.status,
      estObjet(contenu) ? contenu.detail : undefined
    );
  return contenu as T;
}

export async function requete<T>(url: string, init?: RequestInit): Promise<T> {
  try {
    return await json<T>(await fetch(url, init));
  } catch (erreur) {
    if (erreur instanceof ErreurApi) throw erreur;
    if (erreur instanceof TypeError)
      throw new ErreurApi(
        0,
        undefined,
        'Le serveur RULA est indisponible. Réessayez dans quelques instants.'
      );
    throw erreur;
  }
}
