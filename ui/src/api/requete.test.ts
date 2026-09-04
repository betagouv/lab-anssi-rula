import { describe, expect, it } from 'vitest';
import { ErreurApi, json, messageDetail } from './requete';

describe('réponses API', () => {
  it('retourne le JSON valide', async () => {
    await expect(
      json<{ ok: boolean }>(new Response('{"ok":true}'))
    ).resolves.toEqual({
      ok: true,
    });
  });

  it('expose le détail JSON d’une erreur', async () => {
    const promesse = json<never>(
      new Response(JSON.stringify({ detail: 'Albert est indisponible.' }), {
        status: 503,
      })
    );

    await expect(promesse).rejects.toMatchObject({
      name: 'ErreurApi',
      statut: 503,
      message: 'Albert est indisponible.',
    });
  });

  it('assemble le détail structuré des champs', async () => {
    const detail = {
      message: 'Vérifiez les champs obligatoires.',
      champs: ['Le participant est obligatoire.', 'Le transcript est obligatoire.'],
    };
    const promesse = json<never>(
      new Response(JSON.stringify({ detail }), { status: 422 })
    );

    await expect(promesse).rejects.toMatchObject({
      detail,
      message:
        'Vérifiez les champs obligatoires. Le participant est obligatoire. Le transcript est obligatoire.',
    });
  });

  it('transforme une réponse HTML en erreur explicite', async () => {
    const promesse = json<never>(
      new Response('<!DOCTYPE html><html><body>Erreur</body></html>', {
        status: 502,
      })
    );

    await expect(promesse).rejects.toMatchObject({
      statut: 502,
      message: 'Le serveur a renvoyé une réponse invalide (HTTP 502).',
    });
    await expect(promesse).rejects.not.toThrow("Unexpected token '<'");
  });

  it('signale une réponse HTML inattendue sur une réponse réussie', async () => {
    await expect(json<never>(new Response('<!DOCTYPE html>'))).rejects.toEqual(
      new ErreurApi(200, undefined, 'La réponse du serveur est invalide. Réessayez.')
    );
  });

  it('retourne une réponse vide pour un succès 204', async () => {
    await expect(
      json<void>(new Response(null, { status: 204 }))
    ).resolves.toBeUndefined();
  });

  it('fournit un message de repli pour une erreur structurée inconnue', () => {
    expect(messageDetail({ autre: true }, 500)).toBe(
      'Le serveur a renvoyé une réponse invalide (HTTP 500).'
    );
  });
});
