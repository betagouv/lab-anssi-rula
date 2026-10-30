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
  impose?: boolean;
};

export type Masque = {
  identifiant: string;
  valeur_originale: string;
  categorie: CategorieRelecture;
  valeur_anonyme: string;
  actif: boolean;
  impose: boolean;
};

export type PlageEtatRelecture = {
  identifiant: string;
  masque_identifiant: string;
  champ: ChampRelecture;
  debut: number;
  fin: number;
};

export type MasqueEtatRelecture = Omit<Masque, 'valeur_originale' | 'impose'>;

export type InstantaneRelecture = {
  masques: MasqueEtatRelecture[];
  plages: PlageEtatRelecture[];
};

export type EtatRelecture = InstantaneRelecture & {
  selection: string | null;
  annulations: InstantaneRelecture[];
  retablissements: InstantaneRelecture[];
};

type Plage = PlageEtatRelecture & { valeur_originale: string };
type Instantane = { masques: Masque[]; plages: Plage[] };

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
  private annulations: Instantane[] = [];
  private retablissements: Instantane[] = [];
  private readonly occurrencesImposees: Pick<Plage, 'champ' | 'debut' | 'fin'>[];
  selection: string | null;
  revelation: string | null = null;

  constructor(
    readonly contenuOriginal: string,
    readonly contexteOriginal: string,
    occurrences: OccurrenceSource[],
    etat?: EtatRelecture
  ) {
    const identifiants = new Map<string, string>();
    this.masques = [
      ...new Map(
        occurrences.map((occurrence) => {
          const identifiant =
            identifiants.get(occurrence.valeur_originale) ?? crypto.randomUUID();
          identifiants.set(occurrence.valeur_originale, identifiant);
          return [
            occurrence.valeur_originale,
            {
              identifiant,
              valeur_originale: occurrence.valeur_originale,
              categorie: occurrence.categorie,
              valeur_anonyme: occurrence.valeur_anonyme,
              actif: true,
              impose: occurrences.some(
                (candidate) =>
                  candidate.valeur_originale === occurrence.valeur_originale &&
                  candidate.impose
              ),
            },
          ];
        })
      ).values(),
    ];
    this.plages = occurrences.map((occurrence) => {
      if (
        this.source(occurrence.champ).slice(occurrence.debut, occurrence.fin) !==
        occurrence.valeur_originale
      )
        throw new Error('Plage de relecture invalide.');
      return {
        identifiant: crypto.randomUUID(),
        masque_identifiant: identifiants.get(occurrence.valeur_originale)!,
        champ: occurrence.champ,
        debut: occurrence.debut,
        fin: occurrence.fin,
        valeur_originale: occurrence.valeur_originale,
      };
    });
    this.occurrencesImposees = occurrences
      .filter((occurrence) => occurrence.impose)
      .map(({ champ, debut, fin }) => ({ champ, debut, fin }));
    this.selection = this.masques[0]?.identifiant ?? null;
    if (etat) {
      const instantane = this.restaurerInstantane(etat);
      this.masques = instantane.masques;
      this.plages = instantane.plages;
      this.annulations = etat.annulations.map((element) =>
        this.restaurerInstantane(element)
      );
      this.retablissements = etat.retablissements.map((element) =>
        this.restaurerInstantane(element)
      );
      this.selection = this.masques.some(
        (masque) => masque.identifiant === etat.selection
      )
        ? etat.selection
        : (this.masques[0]?.identifiant ?? null);
    }
  }

  lireMasques() {
    return this.masques;
  }

  lireOccurrences() {
    return this.plages.map((plage) => {
      const masque = this.masques.find(
        (element) => element.identifiant === plage.masque_identifiant
      )!;
      return {
        ...plage,
        valeur_affichee: masque.actif
          ? masque.valeur_anonyme
          : masque.valeur_originale,
        impose: masque.impose,
      };
    });
  }

  lireEtat(): EtatRelecture {
    return {
      ...this.etatInstantane(this.instantane()),
      selection: this.selection,
      annulations: this.annulations.map((element) => this.etatInstantane(element)),
      retablissements: this.retablissements.map((element) =>
        this.etatInstantane(element)
      ),
    };
  }

  selectionner(identifiant: string) {
    if (this.masques.some((masque) => masque.identifiant === identifiant))
      this.selection = identifiant;
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

  basculer(identifiant: string) {
    const masque = this.masques.find(
      (element) => element.identifiant === identifiant
    );
    if (!masque || (masque.impose && masque.actif)) return false;
    this.modifier((masques) =>
      masques.map((masque) =>
        masque.identifiant === identifiant
          ? { ...masque, actif: !masque.actif }
          : masque
      )
    );
    this.selectionner(identifiant);
    return true;
  }

  categoriser(identifiant: string, categorie: CategorieRelecture) {
    const masque = this.masques.find(
      (element) => element.identifiant === identifiant
    );
    if (!masque || masque.categorie === categorie) return;
    const pseudo = this.nouveauPseudonyme(categorie);
    this.modifier((masques) =>
      masques.map((element) =>
        element.identifiant === identifiant
          ? { ...element, categorie, valeur_anonyme: pseudo }
          : element
      )
    );
  }

  ajouterValeur(valeur: string, categorie: CategorieRelecture = 'donnee_sensible') {
    if (!valeur.trim()) return false;
    const existant = this.masques.find(
      (masque) => masque.valeur_originale === valeur
    );
    if (existant) {
      this.selection = existant.identifiant;
      return true;
    }
    const plages = this.positions(valeur);
    if (!plages.length || this.chevauche(plages)) return false;
    const identifiant = crypto.randomUUID();
    this.modifier((masques) => [
      ...masques,
      {
        identifiant,
        valeur_originale: valeur,
        categorie,
        valeur_anonyme: this.nouveauPseudonyme(categorie),
        actif: true,
        impose: false,
      },
    ]);
    this.plages = [
      ...this.plages,
      ...plages.map((plage) => ({
        ...plage,
        identifiant: crypto.randomUUID(),
        masque_identifiant: identifiant,
      })),
    ];
    this.selection = identifiant;
    return true;
  }

  annuler() {
    if (!this.annulations.length) return false;
    const precedent = this.annulations[this.annulations.length - 1];
    this.verifierInstantane(precedent);
    this.retablissements.push(this.instantane());
    ({ masques: this.masques, plages: this.plages } = this.annulations.pop()!);
    return true;
  }

  retablir() {
    if (!this.retablissements.length) return false;
    const suivant = this.retablissements[this.retablissements.length - 1];
    this.verifierInstantane(suivant);
    this.annulations.push(this.instantane());
    ({ masques: this.masques, plages: this.plages } = this.retablissements.pop()!);
    return true;
  }

  private nouveauPseudonyme(categorie: CategorieRelecture) {
    const numero =
      Math.max(
        0,
        ...this.masques
          .filter((masque) => masque.categorie === categorie)
          .map((masque) => Number(/_(\d+)\]$/.exec(masque.valeur_anonyme)?.[1] ?? 0))
      ) + 1;
    return `[${categorie.toLocaleUpperCase('fr-FR')}_${String(numero).padStart(2, '0')}]`;
  }

  private positions(valeur: string) {
    return (['transcript', 'contexte'] as const).flatMap((champ) =>
      [...this.source(champ).matchAll(new RegExp(escapeRegex(valeur), 'g'))]
        .filter((match) => match.index !== undefined)
        .filter(
          (match) =>
            champ !== 'transcript' ||
            !chevaucheLocuteur(
              this.source(champ),
              match.index!,
              match.index! + valeur.length
            )
        )
        .map((match) => ({
          champ,
          debut: match.index!,
          fin: match.index! + valeur.length,
          valeur_originale: valeur,
        }))
    );
  }

  private chevauche(plages: Pick<Plage, 'champ' | 'debut' | 'fin'>[]) {
    return plages.some((plage) =>
      this.plages.some(
        (existante) =>
          plage.champ === existante.champ &&
          plage.debut < existante.fin &&
          existante.debut < plage.fin
      )
    );
  }

  private instantane(): Instantane {
    return {
      masques: this.masques.map((masque) => ({ ...masque })),
      plages: this.plages.map((plage) => ({ ...plage })),
    };
  }

  private etatInstantane(instantane: Instantane): InstantaneRelecture {
    return {
      masques: instantane.masques.map(
        ({ identifiant, categorie, valeur_anonyme, actif }) => ({
          identifiant,
          categorie,
          valeur_anonyme,
          actif,
        })
      ),
      plages: instantane.plages.map(
        ({ identifiant, masque_identifiant, champ, debut, fin }) => ({
          identifiant,
          masque_identifiant,
          champ,
          debut,
          fin,
        })
      ),
    };
  }

  private restaurerInstantane(etat: InstantaneRelecture): Instantane {
    if (
      new Set(etat.masques.map((masque) => masque.identifiant)).size !==
        etat.masques.length ||
      new Set(etat.plages.map((plage) => plage.identifiant)).size !==
        etat.plages.length
    )
      throw new Error('État de relecture incompatible.');
    const plages = etat.plages.map((plage) => {
      const valeur_originale = this.source(plage.champ).slice(
        plage.debut,
        plage.fin
      );
      if (!valeur_originale || plage.fin > this.source(plage.champ).length)
        throw new Error('Plage de relecture invalide.');
      return { ...plage, valeur_originale };
    });
    const masques = etat.masques.map((masque) => {
      const plage = plages.find(
        (element) => element.masque_identifiant === masque.identifiant
      );
      if (
        !plage ||
        plages.some(
          (element) =>
            element.masque_identifiant === masque.identifiant &&
            element.valeur_originale !== plage.valeur_originale
        )
      )
        throw new Error('Masque de relecture invalide.');
      return {
        ...masque,
        valeur_originale: plage.valeur_originale,
        impose: false,
      };
    });
    if (
      plages.some(
        (plage) =>
          !masques.some((masque) => masque.identifiant === plage.masque_identifiant)
      )
    )
      throw new Error('Plage de relecture invalide.');
    this.verifierInstantane({ masques, plages });
    for (const masque of masques) {
      masque.impose = plages.some(
        (plage) =>
          plage.masque_identifiant === masque.identifiant &&
          this.occurrencesImposees.some(
            (occurrence) =>
              occurrence.champ === plage.champ &&
              occurrence.debut < plage.fin &&
              plage.debut < occurrence.fin
          )
      );
    }
    return { masques, plages };
  }

  private verifierInstantane(instantane: Instantane) {
    const actives = instantane.plages.filter((plage) =>
      instantane.masques.some(
        (masque) => masque.identifiant === plage.masque_identifiant && masque.actif
      )
    );
    if (
      instantane.plages.some((plage, index) =>
        instantane.plages
          .slice(index + 1)
          .some(
            (autre) =>
              plage.champ === autre.champ &&
              plage.debut < autre.fin &&
              autre.debut < plage.fin
          )
      ) ||
      this.occurrencesImposees.some((obligatoire) => {
        let curseur = obligatoire.debut;
        for (const plage of actives
          .filter((element) => element.champ === obligatoire.champ)
          .sort((a, b) => a.debut - b.debut)) {
          if (plage.debut <= curseur && curseur < plage.fin)
            curseur = Math.max(curseur, plage.fin);
          if (curseur >= obligatoire.fin) break;
        }
        return curseur < obligatoire.fin;
      })
    )
      throw new Error('État de relecture incompatible avec un masque obligatoire.');
  }

  private source(champ: ChampRelecture) {
    return champ === 'transcript' ? this.contenuOriginal : this.contexteOriginal;
  }

  private modifier(operation: (masques: Masque[]) => Masque[]) {
    this.annulations.push(this.instantane());
    if (this.annulations.length > 100) this.annulations.shift();
    this.retablissements = [];
    this.masques = operation(this.masques.map((masque) => ({ ...masque })));
  }
}

export const initialiserEtatRelecture = (
  contenuOriginal: string,
  contexteOriginal: string,
  occurrences: OccurrenceSource[],
  etat?: EtatRelecture
) =>
  new ModeleRelecture(
    contenuOriginal,
    contexteOriginal,
    occurrences,
    etat
  ).lireEtat();

const escapeRegex = (valeur: string) =>
  valeur.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');

const chevaucheLocuteur = (source: string, debut: number, fin: number) =>
  [...source.matchAll(/^SPEAKER_\d{2,}:[ \t]*/gm)].some(
    (repere) => debut < repere.index! + repere[0].length && repere.index! < fin
  );
