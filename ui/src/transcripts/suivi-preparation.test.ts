import { describe, expect, it } from 'vitest';
import { ErreurSuiviPreparation, lirePreparation } from './suivi-preparation';

class ClientPreparationDeTest {
  appels: string[] = [];
  signal: AbortSignal | null = null;

  async get(url: string, signal: AbortSignal, statut = 200): Promise<Response> {
    this.appels.push(url);
    this.signal = signal;
    return new Response(
      JSON.stringify({
        statut: 'termine',
        progression: {
          phase: 'termine',
          groupes_termines: 1,
          groupes_total: 1,
          groupes_en_cours: [],
          duree_secondes: 3,
        },
      }),
      { status: statut }
    );
  }
}

class ReponseLectureAttenteDeTest extends Response {
  constructor(signal: AbortSignal) {
    super('', {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    });
    this.signal = signal;
  }

  private signal: AbortSignal;

  override json(): Promise<unknown> {
    return new Promise((_resolve, reject) => {
      this.signal.addEventListener(
        'abort',
        () => reject(new DOMException('Aborted', 'AbortError')),
        { once: true }
      );
    });
  }
}

describe('suivi d’une préparation', () => {
  it('reprend le jeton avec un GET et retire le délai après réponse', async () => {
    const client = new ClientPreparationDeTest();
    const resultat = await lirePreparation('jeton-test', client.get.bind(client));
    expect(resultat.statut).toBe('termine');
    expect(client.appels).toEqual(['/api/transcripts-pdf/preparation/jeton-test']);
    expect(client.signal?.aborted).toBe(false);
  });

  it('borne le GET et la lecture JSON à dix secondes', async () => {
    const client = {
      get: (_url: string, signal: AbortSignal) =>
        new Promise<Response>((_resolve, reject) => {
          signal.addEventListener(
            'abort',
            () => reject(new DOMException('Aborted', 'AbortError')),
            { once: true }
          );
        }),
    };
    await expect(
      lirePreparation('jeton-test', client.get, undefined, 1)
    ).rejects.toMatchObject({ name: 'AbortError' });
  });

  it('annule aussi la lecture JSON si le délai expire après les en-têtes', async () => {
    const client = {
      get: async (_url: string, signal: AbortSignal) =>
        new ReponseLectureAttenteDeTest(signal),
    };
    const attente = lirePreparation('jeton-test', client.get, undefined, 1);
    await expect(attente).rejects.toMatchObject({ name: 'AbortError' });
  });

  it('distingue un jeton expiré', async () => {
    const client = new ClientPreparationDeTest();
    await expect(
      lirePreparation('jeton-test', (url, signal) => client.get(url, signal, 404))
    ).rejects.toBeInstanceOf(ErreurSuiviPreparation);
  });
});
