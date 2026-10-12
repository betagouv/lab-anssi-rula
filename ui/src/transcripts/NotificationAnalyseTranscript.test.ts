import { render } from 'svelte/server';
import { describe, expect, it } from 'vitest';
import NotificationAnalyseTranscript from './NotificationAnalyseTranscript.svelte';

describe('notification d’analyse de transcript', () => {
  it('indique où consulter une analyse terminée', () => {
    const { body } = render(NotificationAnalyseTranscript, {
      props: { statut: 'prete', voirAnalyse: () => {} },
    });
    expect(body).toContain('role="status"');
    expect(body).toContain('Analyse terminée');
    expect(body).toContain('Analyse générée');
    expect(body).toContain('Voir l’analyse');
  });

  it('indique où consulter une erreur pour réessayer', () => {
    const { body } = render(NotificationAnalyseTranscript, {
      props: { statut: 'echec', voirAnalyse: () => {} },
    });
    expect(body).toContain('L’analyse a échoué');
    expect(body).toContain('Voir l’erreur');
  });
});
