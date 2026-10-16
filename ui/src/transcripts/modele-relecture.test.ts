import { describe, expect, it } from 'vitest';
import { ModeleRelecture } from './modele-relecture';

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
});
