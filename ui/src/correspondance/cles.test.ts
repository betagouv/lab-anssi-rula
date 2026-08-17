import { describe, expect, it } from 'vitest';
import { cleCluster, cleMembre } from './cles';

describe('clés de rendu des correspondances', () => {
  it('génère des clés différentes pour des clusters ayant le même libellé', () => {
    const clusters = [
      { libelle: 'Consulter l’historique des modifications' },
      { libelle: 'Consulter l’historique des modifications' },
    ];

    const cles = clusters.map((cluster, index) => cleCluster(cluster, index));

    expect(new Set(cles).size).toBe(clusters.length);
  });

  it('génère des clés différentes pour des membres ayant la même source et le même texte', () => {
    const membres = [
      {
        source: 'retour_bizdev',
        texte: 'Consulter l’historique des modifications',
      },
      {
        source: 'retour_bizdev',
        texte: 'Consulter l’historique des modifications',
      },
    ];

    const cles = membres.map((membre, index) => cleMembre(membre, index));

    expect(new Set(cles).size).toBe(membres.length);
  });
});
