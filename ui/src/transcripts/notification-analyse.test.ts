import { describe, expect, it } from 'vitest';
import { notificationApresAnalyse } from './notification-analyse';

describe('notification après analyse', () => {
  it('guide vers le résultat si le transcript est affiché à la fin du calcul', () => {
    expect(notificationApresAnalyse('transcript', 'prete')).toBe('prete');
  });

  it('guide vers le message d’erreur si le transcript est affiché à la fin du calcul', () => {
    expect(notificationApresAnalyse('transcript', 'echec')).toBe('echec');
  });

  it('ne détourne pas l’utilisateur de l’analyse déjà affichée', () => {
    expect(notificationApresAnalyse('analyse', 'prete')).toBe('');
  });
});
