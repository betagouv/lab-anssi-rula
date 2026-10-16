export type ChampRelecture = 'transcript' | 'contexte';
export type CategorieRelecture =
  | 'identite'
  | 'coordonnees'
  | 'organisation'
  | 'secret'
  | 'donnee_sensible'
  | 'technologie_ou_produit';

export type OccurrenceSource = {
  identifiant: string;
  valeur_originale: string;
  debut: number;
  fin: number;
  champ: ChampRelecture;
  categorie: CategorieRelecture;
  valeur_anonyme: string;
};

export type Masque = {
  valeur_originale: string;
  categorie: CategorieRelecture;
  valeur_anonyme: string;
  actif: boolean;
};

type Plage = Pick<OccurrenceSource, 'valeur_originale' | 'debut' | 'fin' | 'champ'>;

export const categoriesRelecture: { id: CategorieRelecture; label: string }[] = [
  { id: 'identite', label: 'Identité' },
  { id: 'coordonnees', label: 'Coordonnées' },
  { id: 'organisation', label: 'Organisation' },
  { id: 'secret', label: 'Secret' },
  { id: 'donnee_sensible', label: 'Donnée sensible' },
  { id: 'technologie_ou_produit', label: 'Technologie ou produit' },
];

export class ModeleRelecture {
  private masques: Masque[];
  private plages: Plage[];
  private annulations: { masques: Masque[]; plages: Plage[] }[] = [];
  private retablissements: { masques: Masque[]; plages: Plage[] }[] = [];
  selection: string | null = null;
  revelation: string | null = null;

  constructor(
    readonly contenuOriginal: string,
    readonly contexteOriginal: string,
    occurrences: OccurrenceSource[]
  ) {
    this.plages = occurrences.map(({ valeur_originale, debut, fin, champ }) => {
      if (this.source(champ).slice(debut, fin) !== valeur_originale)
        throw new Error('Plage de relecture invalide.');
      return { valeur_originale, debut, fin, champ };
    });
    this.masques = [
      ...new Map(
        occurrences.map((o) => [
          o.valeur_originale,
          {
            valeur_originale: o.valeur_originale,
            categorie: o.categorie,
            valeur_anonyme: o.valeur_anonyme,
            actif: true,
          },
        ])
      ).values(),
    ];
    this.selection = this.masques[0]?.valeur_originale ?? null;
  }

  lireMasques() {
    return this.masques;
  }

  lireOccurrences() {
    return this.plages.flatMap((plage) => {
      const masque = this.masques.find(
        (m) => m.valeur_originale === plage.valeur_originale
      );
      return masque
        ? [
            {
              ...plage,
              valeur_affichee: masque.actif
                ? masque.valeur_anonyme
                : masque.valeur_originale,
            },
          ]
        : [];
    });
  }

  projeter(champ: ChampRelecture) {
    return this.lireOccurrences()
      .filter((plage) => plage.champ === champ)
      .sort((a, b) => b.debut - a.debut)
      .reduce(
        (texte, plage) =>
          `${texte.slice(0, plage.debut)}${plage.valeur_affichee}${texte.slice(plage.fin)}`,
        this.source(champ)
      );
  }

  basculer(valeur: string) {
    this.modifier((masques) =>
      masques.map((m) =>
        m.valeur_originale === valeur ? { ...m, actif: !m.actif } : m
      )
    );
  }

  categoriser(valeur: string, categorie: CategorieRelecture) {
    const masque = this.masques.find((m) => m.valeur_originale === valeur);
    if (!masque || masque.categorie === categorie) return;
    const pseudo = this.nouveauPseudonyme(categorie);
    this.modifier((masques) =>
      masques.map((m) =>
        m.valeur_originale === valeur
          ? { ...m, categorie, valeur_anonyme: pseudo }
          : m
      )
    );
  }

  ajouterValeur(valeur: string, categorie: CategorieRelecture = 'donnee_sensible') {
    if (!valeur.trim()) return false;
    if (this.masques.some((m) => m.valeur_originale === valeur)) {
      this.selection = valeur;
      return true;
    }
    const plages = this.positions(valeur);
    if (!plages.length) return false;
    if (this.chevauche(plages)) return false;
    this.modifier((masques) => [
      ...masques,
      {
        valeur_originale: valeur,
        categorie,
        valeur_anonyme: this.nouveauPseudonyme(categorie),
        actif: true,
      },
    ]);
    this.plages = [...this.plages, ...plages];
    this.selection = valeur;
    return true;
  }

  annuler() {
    if (!this.annulations.length) return false;
    this.retablissements.push(this.instantane());
    ({ masques: this.masques, plages: this.plages } = this.annulations.pop()!);
    return true;
  }

  retablir() {
    if (!this.retablissements.length) return false;
    this.annulations.push(this.instantane());
    ({ masques: this.masques, plages: this.plages } = this.retablissements.pop()!);
    return true;
  }

  private nouveauPseudonyme(categorie: CategorieRelecture) {
    const numero =
      Math.max(
        0,
        ...this.masques
          .filter((m) => m.categorie === categorie)
          .map((m) => Number(/_(\d+)\]$/.exec(m.valeur_anonyme)?.[1] ?? 0))
      ) + 1;
    return `[${categorie.toLocaleUpperCase('fr-FR')}_${String(numero).padStart(2, '0')}]`;
  }

  private positions(valeur: string) {
    return (['transcript', 'contexte'] as const).flatMap((champ) =>
      [...this.source(champ).matchAll(new RegExp(escapeRegex(valeur), 'g'))]
        .filter((m) => m.index !== undefined)
        .filter(
          (m) =>
            champ !== 'transcript' ||
            !chevaucheLocuteur(
              this.source(champ),
              m.index!,
              m.index! + valeur.length
            )
        )
        .map((m) => ({
          champ,
          valeur_originale: valeur,
          debut: m.index!,
          fin: m.index! + valeur.length,
        }))
    );
  }

  private chevauche(plages: Plage[]) {
    return plages.some((plage) =>
      this.plages.some(
        (existante) =>
          plage.champ === existante.champ &&
          plage.debut < existante.fin &&
          existante.debut < plage.fin
      )
    );
  }

  private instantane() {
    return {
      masques: this.masques.map((m) => ({ ...m })),
      plages: this.plages.map((p) => ({ ...p })),
    };
  }

  private source(champ: ChampRelecture) {
    return champ === 'transcript' ? this.contenuOriginal : this.contexteOriginal;
  }

  private modifier(operation: (masques: Masque[]) => Masque[]) {
    this.annulations.push(this.instantane());
    this.retablissements = [];
    this.masques = operation(this.masques.map((m) => ({ ...m })));
  }
}

const escapeRegex = (valeur: string) =>
  valeur.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');

const chevaucheLocuteur = (source: string, debut: number, fin: number) =>
  [...source.matchAll(/^SPEAKER_\d{2}:[ \t]*/gm)].some(
    (repere) => debut < repere.index! + repere[0].length && repere.index! < fin
  );
