export type LocuteurRelecture = {
  identifiant: string;
  role: 'interne' | 'externe' | 'indetermine';
  justification: string;
  nom_affiche?: string;
};

export type SegmentLocuteur =
  | { type: 'texte'; texte: string }
  | { type: 'locuteur'; identifiant: string; texte: string };

export function decouperLocuteurs(
  texte: string,
  locuteurs: LocuteurRelecture[]
): SegmentLocuteur[] {
  const segments: SegmentLocuteur[] = [];
  let debut = 0;
  for (const correspondance of texte.matchAll(/SPEAKER_\d{2}:/g)) {
    const position = correspondance.index!;
    if (position > debut)
      segments.push({ type: 'texte', texte: texte.slice(debut, position) });
    const identifiant = correspondance[0].slice(0, -1);
    const index = locuteurs.findIndex(
      (locuteur) => locuteur.identifiant === identifiant
    );
    const locuteur = locuteurs[index];
    const role =
      locuteur?.role === 'interne'
        ? 'Interne'
        : locuteur?.role === 'externe'
          ? 'Externe'
          : 'Indéterminé';
    const numero = Number(identifiant.slice(-2));
    segments.push({
      type: 'locuteur',
      identifiant,
      texte: locuteur
        ? locuteur.nom_affiche?.trim() || role + ' · ' + numero
        : identifiant,
    });
    debut = position + correspondance[0].length;
  }
  if (debut < texte.length)
    segments.push({ type: 'texte', texte: texte.slice(debut) });
  return segments;
}
