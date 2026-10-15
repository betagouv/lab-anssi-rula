import { render } from 'svelte/server';
import { describe, expect, it } from 'vitest';
import ResultatAnalyse from './ResultatAnalyse.svelte';

describe('rendu d’une analyse de transcript PDF', () => {
  it('affiche le résumé, les verbatims et les points saillants', () => {
    const { body } = render(ResultatAnalyse, {
      props: {
        contenu: {
          resume: 'Synthèse utilisateur',
          themes: ['Gestion des droits'],
          points_positifs: [
            {
              description: 'La synthèse est pratique',
              verbatim: 'C’est très pratique.',
              speaker_id: 'SPEAKER_01',
              tour_id: 4,
              sentiment: 'positif',
              gravite: 'faible',
            },
          ],
          points_negatifs: [
            {
              description: 'La gestion est répétitive',
              sentiment: 'négatif',
              gravite: 'élevée',
            },
          ],
        },
      },
    });
    expect(body).toContain('Synthèse utilisateur');
    expect(body).toContain('Gestion des droits');
    expect(body).toContain('C’est très pratique.');
    expect(body).toContain('<p>Sentiment : positif</p>');
    expect(body).toContain('<p>Gravité : faible</p>');
    expect(body).toContain('<p>Sentiment : négatif</p>');
    expect(body).toContain('<p>Gravité : élevée</p>');
    expect(body).not.toContain('· Gravité');
  });

  it('affiche un compte rendu produit sans répéter la liste technique des fonctionnalités', () => {
    const { body } = render(ResultatAnalyse, {
      props: {
        contenu: {
          contexte: {
            produit: 'Portail synthétique',
            profil_utilisateur: 'Gestionnaire',
            objectif: 'Comprendre la recherche',
          },
          ouverture: 'La personne perd du temps à retrouver les dossiers.',
          points_cles: ['La recherche est le principal irritant.'],
          profil: [],
          sujets: [
            {
              titre: 'Retrouver un dossier',
              constat: 'La recherche échoue sur les noms composés.',
              enseignements: [
                {
                  description: 'La personne ne retrouve pas les dossiers composés.',
                  nature: 'fait',
                  verbatim: 'Je ne retrouve pas le dossier Dupont Martin.',
                  speaker_id: 'SPEAKER_01',
                  tour_id: 2,
                },
                {
                  description: 'Le découpage du nom peut être lié.',
                  nature: 'hypothese',
                  verbatim: 'Je ne retrouve pas le dossier Dupont Martin.',
                  speaker_id: 'SPEAKER_01',
                  tour_id: 2,
                },
                {
                  description: 'Tester une recherche tolérante.',
                  nature: 'interpretation',
                  verbatim: 'Je ne retrouve pas le dossier Dupont Martin.',
                  speaker_id: 'SPEAKER_01',
                  tour_id: 2,
                },
              ],
            },
          ],
          pistes: [
            {
              action: 'Étudier une recherche tolérante',
              besoin: 'Retrouver les dossiers',
              origine: 'proposition_analyste',
              effort_estime: 'Non estimé',
            },
          ],
          prochaines_etapes: [
            {
              action: 'Tester',
              verification: 'Cas composé couvert',
              verbatim: 'Je ne retrouve pas le dossier Dupont Martin.',
              speaker_id: 'SPEAKER_01',
              tour_id: 2,
            },
          ],
          fonctionnalites: [
            { action: 'Rechercher', verbatim: 'Rechercher par nom' },
          ],
        },
      },
    });

    expect(body).toContain('Synthèse');
    expect(body).toContain('La recherche est le principal irritant.');
    expect(body).toContain('Fait :');
    expect(body).toContain('Hypothèse :');
    expect(body).toContain('Interprétation :');
    expect(body).toContain('Je ne retrouve pas le dossier Dupont Martin.');
    expect(body).toContain('Non estimé');
    expect(body).not.toContain('Fonctionnalités évoquées');
  });

  it('conserve le rendu résumé/extractions des analyses BizDev historiques', () => {
    const { body } = render(ResultatAnalyse, {
      props: {
        contenu: {
          resume: 'Le partenaire veut clarifier le pilote.',
          themes: ['Périmètre'],
          enjeux: [{ description: 'La validation interne prend du temps.' }],
          fonctionnalites: [],
        },
      },
    });

    expect(body).toContain('Le partenaire veut clarifier le pilote.');
    expect(body).toContain('La validation interne prend du temps.');
  });
});
