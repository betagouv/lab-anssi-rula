import { describe, expect, it } from 'vitest';
import { initialiserEtatRelecture, ModeleRelecture } from './modele-relecture';

const occurrencesDans = (contenu: string, contexte: string, valeurs = ['Alice']) =>
  valeurs.flatMap((valeur, index) =>
    (['transcript', 'contexte'] as const).flatMap((champ) => {
      const source = champ === 'transcript' ? contenu : contexte;
      return [...source.matchAll(new RegExp(valeur, 'g'))].map((repere) => ({
        identifiant: `${index}-${champ}-${repere.index}`,
        valeur_originale: valeur,
        debut: repere.index!,
        fin: repere.index! + valeur.length,
        champ,
        categorie: 'identite' as const,
        valeur_anonyme: `[IDENTITE_${String(index + 1).padStart(2, '0')}]`,
      }));
    })
  );

describe('modèle de relecture pseudonymisation', () => {
  it('projette toutes les mentions exactes dans les deux champs et conserve les offsets UTF-16', () => {
    const modele = new ModeleRelecture(
      'SPEAKER_01: 🧑‍💻 Alice, Alice.',
      'Équipe Alice',
      occurrencesDans('SPEAKER_01: 🧑‍💻 Alice, Alice.', 'Équipe Alice')
    );
    expect(modele.projeter('transcript')).toBe(
      'SPEAKER_01: 🧑‍💻 [IDENTITE_01], [IDENTITE_01].'
    );
    expect(modele.projeter('contexte')).toBe('Équipe [IDENTITE_01]');
    expect(modele.lireOccurrences().map((o) => o.debut)).toEqual([18, 25, 7]);
  });

  it('initialise la relecture sans état serveur et conserve un état déjà sauvegardé', () => {
    const contenu = 'Alice parle à Bob';
    const occurrences = occurrencesDans(contenu, '', ['Alice', 'Bob']);
    const initial = initialiserEtatRelecture(contenu, '', occurrences);
    const modeleInitial = new ModeleRelecture(contenu, '', [], initial);
    expect(modeleInitial.projeter('transcript')).toBe(
      '[IDENTITE_01] parle à [IDENTITE_02]'
    );
    modeleInitial.categoriser(modeleInitial.lireMasques()[0].identifiant, 'secret');
    const sauvegarde = initialiserEtatRelecture(
      contenu,
      '',
      occurrences,
      modeleInitial.lireEtat()
    );
    const modeleRestaure = new ModeleRelecture(contenu, '', [], sauvegarde);
    expect(modeleRestaure.projeter('transcript')).toBe(
      '[SECRET_01] parle à [IDENTITE_02]'
    );
  });

  it('initialise la relecture et projette le transcript sans occurrence', () => {
    const contenu = 'Transcript sans occurrence détectée.';
    const etat = initialiserEtatRelecture(contenu, 'Contexte sans masque.', []);
    const modele = new ModeleRelecture(contenu, 'Contexte sans masque.', [], etat);
    expect(modele.lireMasques()).toEqual([]);
    expect(modele.projeter('transcript')).toBe(contenu);
    expect(modele.projeter('contexte')).toBe('Contexte sans masque.');
  });

  it('active et désactive globalement un masque, avec annulation et rétablissement', () => {
    const modele = new ModeleRelecture(
      'Alice et Alice',
      'Alice',
      occurrencesDans('Alice et Alice', 'Alice')
    );
    modele.basculer(modele.lireMasques()[0].identifiant);
    expect(modele.projeter('transcript')).toBe('Alice et Alice');
    expect(modele.projeter('contexte')).toBe('Alice');
    modele.annuler();
    expect(modele.projeter('transcript')).toBe('[IDENTITE_01] et [IDENTITE_01]');
    modele.retablir();
    expect(modele.projeter('contexte')).toBe('Alice');
  });

  it('ajoute un masque sur toutes les mentions exactes et refuse un chevauchement partiel', () => {
    const modele = new ModeleRelecture(
      'Alice Dupont et Alice Dupont',
      '',
      occurrencesDans('Alice Dupont et Alice Dupont', '')
    );
    expect(modele.ajouterValeur('Alice Dupont')).toBe(false);
    expect(modele.lireMasques()).toHaveLength(1);
    expect(modele.ajouterValeur('Dupont')).toBe(true);
    expect(modele.lireMasques()).toHaveLength(2);
    expect(modele.annuler()).toBe(true);
    expect(modele.lireMasques()).toHaveLength(1);
  });

  it('modifie une catégorie sans renuméroter les autres et restaure exactement la catégorie', () => {
    const modele = new ModeleRelecture('Alice Bob', '', [
      ...occurrencesDans('Alice Bob', '', ['Alice', 'Bob']),
    ]);
    modele.categoriser(modele.lireMasques()[0].identifiant, 'secret');
    expect(modele.lireMasques().map((m) => m.valeur_anonyme)).toEqual([
      '[SECRET_01]',
      '[IDENTITE_02]',
    ]);
    modele.annuler();
    expect(modele.lireMasques()[0].valeur_anonyme).toBe('[IDENTITE_01]');
  });

  it('garde les correspondances sensibles à la casse et refuse un masque inactif', () => {
    const modele = new ModeleRelecture(
      'Alice Dupont et alice Dupont',
      '',
      occurrencesDans('Alice Dupont et alice Dupont', '')
    );
    modele.basculer(modele.lireMasques()[0].identifiant);
    expect(modele.ajouterValeur('lic')).toBe(false);
    expect(modele.ajouterValeur('alice')).toBe(true);
    expect(modele.projeter('transcript')).toBe(
      'Alice Dupont et [DONNEE_SENSIBLE_01] Dupont'
    );
  });

  it('efface la branche de rétablissement après une nouvelle modification', () => {
    const modele = new ModeleRelecture(
      'Alice, Bob et Carol',
      '',
      occurrencesDans('Alice, Bob et Carol', '')
    );
    expect(modele.ajouterValeur('Bob')).toBe(true);
    expect(modele.annuler()).toBe(true);
    expect(modele.ajouterValeur('Carol')).toBe(true);
    expect(modele.retablir()).toBe(false);
    expect(modele.projeter('transcript')).toBe(
      '[IDENTITE_01], Bob et [DONNEE_SENSIBLE_01]'
    );
  });

  it('restaure les plages, catégories, masques et historique sans sérialiser le texte source', () => {
    const texte = 'Élodie a choisi Alice';
    const contexte = 'Alice est aussi citée';
    const modele = new ModeleRelecture(
      texte,
      contexte,
      occurrencesDans(texte, contexte, ['Élodie', 'Alice'])
    );
    const alice = modele
      .lireMasques()
      .find((masque) => masque.valeur_originale === 'Alice')!;
    modele.categoriser(alice.identifiant, 'organisation');
    modele.basculer(alice.identifiant);
    expect(modele.ajouterValeur('choisi', 'identite')).toBe(true);
    const etat = modele.lireEtat();
    expect(JSON.stringify(etat)).not.toContain(texte);
    expect(JSON.stringify(etat)).not.toContain(contexte);
    const restaure = new ModeleRelecture(texte, contexte, [], etat);
    expect(restaure.projeter('transcript')).toBe(modele.projeter('transcript'));
    expect(restaure.projeter('contexte')).toBe(modele.projeter('contexte'));
    expect(restaure.lireMasques()).toEqual(modele.lireMasques());
    expect(restaure.annuler()).toBe(true);
    expect(
      restaure.lireMasques().some((masque) => masque.valeur_originale === 'choisi')
    ).toBe(false);
  });

  it('préserve les masques obligatoires au toggle, dans l’historique et à la reprise', () => {
    const texte = 'Secret et Secret';
    const occurrences = occurrencesDans(texte, '', ['Secret']).map((occurrence) => ({
      ...occurrence,
      impose: true,
    }));
    const modele = new ModeleRelecture(texte, '', occurrences);
    const identifiant = modele.lireMasques()[0].identifiant;

    expect(modele.lireMasques()[0].impose).toBe(true);
    expect(modele.basculer(identifiant)).toBe(false);
    expect(modele.annuler()).toBe(false);
    expect(modele.projeter('transcript')).toBe('[IDENTITE_01] et [IDENTITE_01]');
    modele.categoriser(identifiant, 'secret');
    expect(modele.lireMasques()[0].impose).toBe(true);
    expect(modele.annuler()).toBe(true);
    expect(modele.lireMasques()[0].impose).toBe(true);
    expect(modele.retablir()).toBe(true);
    expect(modele.lireMasques()[0].impose).toBe(true);

    const etat = modele.lireEtat();
    expect(JSON.stringify(etat)).not.toContain('impose');
    const reprise = new ModeleRelecture(texte, '', occurrences, etat);
    expect(reprise.lireMasques()[0].impose).toBe(true);
    expect(reprise.basculer(identifiant)).toBe(false);
  });

  it('refuse une sélection partiellement chevauchante sans entrée d’historique', () => {
    const texte = 'Secret et public';
    const occurrences = occurrencesDans(texte, '', ['Secret']).map((occurrence) => ({
      ...occurrence,
      impose: true,
    }));
    const modele = new ModeleRelecture(texte, '', occurrences);

    expect(modele.ajouterValeur('ecre')).toBe(false);
    expect(modele.lireMasques()).toHaveLength(1);
    expect(modele.annuler()).toBe(false);
    expect(modele.projeter('transcript')).toBe('[IDENTITE_01] et public');
  });

  it('refuse un état de reprise qui tronque la couverture obligatoire', () => {
    const texte = 'Secret';
    const occurrences = occurrencesDans(texte, '', ['Secret']).map((occurrence) => ({
      ...occurrence,
      impose: true,
    }));
    const etat = initialiserEtatRelecture(texte, '', occurrences);
    etat.plages[0].debut = 1;

    expect(() => new ModeleRelecture(texte, '', occurrences, etat)).toThrow(
      'État de relecture incompatible avec un masque obligatoire.'
    );
  });
});
