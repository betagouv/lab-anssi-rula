import { render } from 'svelte/server';
import { describe, expect, it } from 'vitest';
import PanneauAnalyseTranscript from './PanneauAnalyseTranscript.svelte';

const lancer = () => {};

describe('panneau d’analyse de transcript', () => {
  it('indique où le résultat apparaîtra avant le lancement', () => {
    const { body } = render(PanneauAnalyseTranscript, {
      props: {
        contenu: null,
        chargement: false,
        desactive: false,
        erreur: '',
        relancer: false,
        lancer,
      },
    });
    expect(body).toContain('Après lancement');
    expect(body).toContain('Lancer l’analyse');
  });

  it('affiche le statut accessible et désactive le bouton pendant le calcul', () => {
    const { body } = render(PanneauAnalyseTranscript, {
      props: {
        contenu: null,
        chargement: true,
        desactive: true,
        erreur: '',
        relancer: false,
        lancer,
      },
    });
    expect(body).toContain('role="status"');
    expect(body).toContain('Analyse en cours');
    expect(body).toContain('aria-busy="true"');
    expect(body).toContain('disabled');
  });

  it('affiche les erreurs et propose de relancer', () => {
    const { body } = render(PanneauAnalyseTranscript, {
      props: {
        contenu: null,
        chargement: false,
        desactive: false,
        erreur: 'L’analyse a échoué.',
        relancer: true,
        lancer,
      },
    });
    expect(body).toContain('role="alert"');
    expect(body).toContain('L’analyse a échoué.');
    expect(body).toContain('Relancer l’analyse');
  });

  it('affiche le résultat directement dans le panneau', () => {
    const { body } = render(PanneauAnalyseTranscript, {
      props: {
        contenu: { resume: 'Synthèse prête' },
        chargement: false,
        desactive: false,
        erreur: '',
        relancer: false,
        lancer,
      },
    });
    expect(body).toContain('Synthèse prête');
    expect(body).not.toContain('Lancer l’analyse');
  });
});
