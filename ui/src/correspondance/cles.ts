import type { Cluster, Membre } from '../types';

/**
 * Génère une clé unique dans la liste des clusters, y compris lorsque deux
 * clusters ont le même libellé renvoyé par l'API.
 */
export function cleCluster(
  cluster: Pick<Cluster, 'libelle'>,
  index: number
): string {
  return `${cluster.libelle}-${index}`;
}

/**
 * Génère une clé unique dans la liste des membres d'un cluster, y compris
 * lorsque plusieurs membres ont la même source et le même texte.
 */
export function cleMembre(
  membre: Pick<Membre, 'source' | 'texte'>,
  index: number
): string {
  return `${membre.source}-${membre.texte}-${index}`;
}
