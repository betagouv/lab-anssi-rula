import type { PassageTransverse } from '../api/analyse_transverse';

export function libelleSource(source: PassageTransverse['source']) {
  if (source === 'transcript') return 'Transcript';
  if (source === 'transcript_produit') return 'Transcript produit';
  if (source === 'transcript_bizdev') return 'Transcript BizDev';
  return source === 'idee' ? 'FeatureBase' : 'BizDev';
}

export function lienPassage(passage: PassageTransverse) {
  if (
    (passage.source === 'transcript' || passage.source === 'transcript_produit') &&
    passage.projet_id &&
    passage.transcript_id
  )
    return `#/projets/${passage.projet_id}/entretiens/${passage.transcript_id}`;
  if (passage.source === 'idee' && passage.source_id)
    return `#/sources/featurebase/${passage.source_id}`;
  if (passage.source === 'retour_bizdev' && passage.source_id)
    return `#/sources/retours-bizdev/${passage.source_id}`;
  return null;
}
