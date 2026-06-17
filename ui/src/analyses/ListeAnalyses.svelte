<script lang="ts">
  import { marked } from 'marked';
  import type { Vue, Transcript, Analyse, Fonctionnalite } from '../types';
  import { listerAnalyses, genererAnalyse } from '../api/analyses';
  import {
    listerFonctionnalites,
    calculerFonctionnalites,
  } from '../api/fonctionnalites';
  import { listerTranscripts } from '../api/transcripts';

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  let { onnaviquer }: { onnaviquer: (v: Vue) => void } = $props();

  type Ressource = { id: number; nom: string };
  type Ligne = {
    transcript: Transcript;
    analyse: Analyse | null;
    enCoursAnalyse: boolean;
    fonctionnalites: Fonctionnalite[] | null;
    enCoursFonctionnalites: boolean;
  };

  let lignes = $state<Ligne[]>([]);
  let identiteParId = $state<Record<number, string>>({});
  let produitParId = $state<Record<number, string>>({});
  let chargement = $state(true);
  let analyseOuverte = $state<number | null>(null);
  let fonctionnalitesOuverte = $state<number | null>(null);

  $effect(() => {
    Promise.all([
      listerTranscripts(),
      listerAnalyses(),
      listerFonctionnalites(),
      fetch('/api/identites').then((r) => r.json() as Promise<Ressource[]>),
      fetch('/api/produits').then((r) => r.json() as Promise<Ressource[]>),
    ]).then(([ts, as, fs, ids, prods]) => {
      const analyseParTranscript = Object.fromEntries(
        as.map((a) => [a.transcript_id, a])
      );
      const fonctionnalitesParTranscript: Record<number, Fonctionnalite[]> = {};
      fs.forEach((f) => {
        (fonctionnalitesParTranscript[f.transcript_id] ??= []).push(f);
      });
      lignes = ts.map((t) => ({
        transcript: t,
        analyse: analyseParTranscript[t.id] ?? null,
        enCoursAnalyse: false,
        fonctionnalites: fonctionnalitesParTranscript[t.id] ?? null,
        enCoursFonctionnalites: false,
      }));
      identiteParId = Object.fromEntries(ids.map((i) => [i.id, i.nom]));
      produitParId = Object.fromEntries(prods.map((p) => [p.id, p.nom]));
      chargement = false;
    });
  });

  async function analyser(index: number) {
    lignes[index] = { ...lignes[index], enCoursAnalyse: true };
    try {
      const analyse = await genererAnalyse(lignes[index].transcript.id);
      lignes[index] = { ...lignes[index], analyse, enCoursAnalyse: false };
      analyseOuverte = lignes[index].transcript.id;
      fonctionnalitesOuverte = null;
    } catch {
      lignes[index] = { ...lignes[index], enCoursAnalyse: false };
    }
  }

  async function calculer(index: number) {
    lignes[index] = { ...lignes[index], enCoursFonctionnalites: true };
    try {
      const fonctionnalites = await calculerFonctionnalites(
        lignes[index].transcript.id
      );
      lignes[index] = {
        ...lignes[index],
        fonctionnalites,
        enCoursFonctionnalites: false,
      };
      fonctionnalitesOuverte = lignes[index].transcript.id;
      analyseOuverte = null;
    } catch {
      lignes[index] = { ...lignes[index], enCoursFonctionnalites: false };
    }
  }

  function toggleAnalyse(transcriptId: number) {
    analyseOuverte = analyseOuverte === transcriptId ? null : transcriptId;
    fonctionnalitesOuverte = null;
  }

  function toggleFonctionnalites(transcriptId: number) {
    fonctionnalitesOuverte =
      fonctionnalitesOuverte === transcriptId ? null : transcriptId;
    analyseOuverte = null;
  }
</script>

<div class="fr-container fr-py-4w">
  <h1 class="fr-h2">Analyses</h1>

  {#if chargement}
    <p>Chargement…</p>
  {:else if lignes.length === 0}
    <p class="fr-text--lg">Aucun transcript enregistré pour l'instant.</p>
  {:else}
    <div class="fr-table fr-table--bordered">
      <table>
        <thead>
          <tr>
            <th scope="col">Date</th>
            <th scope="col">Identité</th>
            <th scope="col">Projet</th>
            <th scope="col">Analyse</th>
            <th scope="col">Fonctionnalités</th>
          </tr>
        </thead>
        <tbody>
          {#each lignes as ligne, i (ligne.transcript.id)}
            <tr>
              <td>{ligne.transcript.date_entretien}</td>
              <td
                >{identiteParId[ligne.transcript.identite_id] ??
                  ligne.transcript.identite_id}</td
              >
              <td
                >{produitParId[ligne.transcript.produit_id] ??
                  ligne.transcript.produit_id}</td
              >
              <td>
                <div class="actions">
                  {#if ligne.enCoursAnalyse}
                    <span class="fr-badge fr-badge--info">En cours…</span>
                  {:else if ligne.analyse}
                    <button
                      class="fr-btn fr-btn--secondary fr-btn--sm"
                      type="button"
                      onclick={() => toggleAnalyse(ligne.transcript.id)}
                    >
                      {analyseOuverte === ligne.transcript.id
                        ? 'Masquer'
                        : "Voir l'analyse"}
                    </button>
                  {:else}
                    <button
                      class="fr-btn fr-btn--sm"
                      type="button"
                      onclick={() => analyser(i)}
                    >
                      Analyser
                    </button>
                  {/if}
                </div>
              </td>
              <td>
                <div class="actions">
                  {#if ligne.enCoursFonctionnalites}
                    <span class="fr-badge fr-badge--info">En cours…</span>
                  {:else if ligne.fonctionnalites}
                    <button
                      class="fr-btn fr-btn--secondary fr-btn--sm"
                      type="button"
                      onclick={() => toggleFonctionnalites(ligne.transcript.id)}
                    >
                      {fonctionnalitesOuverte === ligne.transcript.id
                        ? 'Masquer'
                        : `${ligne.fonctionnalites.length} fonctionnalité(s)`}
                    </button>
                  {:else}
                    <button
                      class="fr-btn fr-btn--sm"
                      type="button"
                      onclick={() => calculer(i)}
                    >
                      Calculer
                    </button>
                  {/if}
                </div>
              </td>
            </tr>
            {#if analyseOuverte === ligne.transcript.id && ligne.analyse}
              <tr class="ligne-detail">
                <td colspan="5">
                  <div class="analyse-contenu">
                    <!-- eslint-disable-next-line svelte/no-at-html-tags -->
                    {@html marked.parse(ligne.analyse.contenu)}
                  </div>
                </td>
              </tr>
            {/if}
            {#if fonctionnalitesOuverte === ligne.transcript.id && ligne.fonctionnalites}
              <tr class="ligne-detail">
                <td colspan="5">
                  <ul class="fonctionnalites-liste">
                    {#each ligne.fonctionnalites as f (f.id)}
                      <li>{f.contenu}</li>
                    {/each}
                  </ul>
                </td>
              </tr>
            {/if}
          {/each}
        </tbody>
      </table>
    </div>
  {/if}
</div>

<style>
  .actions {
    display: flex;
    gap: 0.5rem;
  }
  .ligne-detail td {
    background: var(--background-alt-grey, #f6f6f6);
    padding: 1.5rem;
  }
  .analyse-contenu {
    max-width: 900px;
  }
  .analyse-contenu :global(h1),
  .analyse-contenu :global(h2),
  .analyse-contenu :global(h3) {
    font-weight: bold;
    margin: 1rem 0 0.5rem;
  }
  .analyse-contenu :global(ul),
  .analyse-contenu :global(ol) {
    padding-left: 1.5rem;
    margin: 0.5rem 0;
  }
  .analyse-contenu :global(p) {
    margin: 0.5rem 0;
  }
  .fonctionnalites-liste {
    padding-left: 1.5rem;
    margin: 0;
  }
  .fonctionnalites-liste li {
    margin: 0.25rem 0;
  }
</style>
