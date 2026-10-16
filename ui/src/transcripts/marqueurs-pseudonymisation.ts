export const CATEGORIES_PSEUDONYMISATION = [
  { code: 'IDENTITE', id: 'identite', libelle: 'Identité' },
  { code: 'COORDONNEES', id: 'coordonnees', libelle: 'Coordonnées' },
  { code: 'ORGANISATION', id: 'organisation', libelle: 'Organisation' },
  { code: 'SECRET', id: 'secret', libelle: 'Secret' },
  {
    code: 'DONNEE_SENSIBLE',
    id: 'donnee-sensible',
    libelle: 'Donnée sensible',
  },
  {
    code: 'TECHNOLOGIE_OU_PRODUIT',
    id: 'technologie-ou-produit',
    libelle: 'Technologie ou produit',
  },
] as const;

export type CategoriePseudonymisation = (typeof CATEGORIES_PSEUDONYMISATION)[number];

export type SegmentTranscript = {
  texte: string;
  categorie: CategoriePseudonymisation | null;
};

const marqueur =
  /\[(IDENTITE|COORDONNEES|ORGANISATION|SECRET|DONNEE_SENSIBLE|TECHNOLOGIE_OU_PRODUIT)_\d{2,}\]/g;

export function decouperTranscriptPseudonymise(texte: string): SegmentTranscript[] {
  const segments: SegmentTranscript[] = [];
  let position = 0;

  for (const correspondance of texte.matchAll(marqueur)) {
    const debut = correspondance.index;
    if (debut > position) {
      segments.push({ texte: texte.slice(position, debut), categorie: null });
    }
    segments.push({
      texte: correspondance[0],
      categorie:
        CATEGORIES_PSEUDONYMISATION.find(
          (categorie) => categorie.code === correspondance[1]
        ) ?? null,
    });
    position = debut + correspondance[0].length;
  }

  if (position < texte.length) {
    segments.push({ texte: texte.slice(position), categorie: null });
  }

  return segments;
}
