import { afterEach, expect, it, vi } from 'vitest';
import {
  listerRapportsClaude,
  listerTranscriptsClaude,
  lireRapportClaude,
} from './rapports_claude';

afterEach(() => vi.unstubAllGlobals());

it('parcourt le catalogue et l’historique puis assemble le rapport par blocs', async () => {
  const urls: string[] = [];
  const reponses = [
    { elements: [{ id: 1 }], curseur_suivant: 1 },
    { elements: [{ id: 2 }], curseur_suivant: null },
    { elements: [{ id: 8 }], curseur_suivant: 8 },
    { elements: [{ id: 9 }], curseur_suivant: null },
    {
      rapport_id: 9,
      transcript_id: 2,
      cree_le: '2026-10-19T10:00:00Z',
      courant: true,
      bloc: 'Première ',
      offset_suivant: 9,
    },
    {
      rapport_id: 9,
      transcript_id: 2,
      cree_le: '2026-10-19T10:00:00Z',
      courant: true,
      bloc: 'seconde partie',
      offset_suivant: null,
    },
  ];
  vi.stubGlobal(
    'fetch',
    vi.fn(async (url: string) => {
      urls.push(url);
      return new Response(JSON.stringify(reponses.shift()), { status: 200 });
    })
  );

  await expect(listerTranscriptsClaude(7, 'produit')).resolves.toMatchObject({
    elements: [{ id: 1 }, { id: 2 }],
  });
  await expect(listerRapportsClaude(2)).resolves.toMatchObject({
    elements: [{ id: 8 }, { id: 9 }],
  });
  await expect(lireRapportClaude(9)).resolves.toMatchObject({
    transcript_id: 2,
    contenu: 'Première seconde partie',
  });
  expect(urls).toHaveLength(6);
  expect(urls[1]).toContain('curseur=1');
});
