<script lang="ts">
  import { SvelteSet } from 'svelte/reactivity';
  import type { Cluster, Vue } from '../types';
  import {
    chargerCorrespondances,
    analyserCorrespondances,
  } from '../api/correspondances';

  let { onnaviquer }: { onnaviquer: (v: Vue) => void } = $props();

  let clusters = $state<Cluster[]>([]);
  let analyse = $state(false);
  let enCours = $state(false);
  let erreur = $state<string | null>(null);
  const verbatimsOuverts = new SvelteSet<string>();

  $effect(() => {
    chargerCorrespondances().then((data) => {
      if (data.length > 0) {
        clusters = data;
        analyse = true;
      }
    });
  });

  function toggleVerbatim(cle: string) {
    if (verbatimsOuverts.has(cle)) {
      verbatimsOuverts.delete(cle);
    } else {
      verbatimsOuverts.add(cle);
    }
  }

  async function analyser() {
    enCours = true;
    erreur = null;
    try {
      clusters = await analyserCorrespondances();
      analyse = true;
    } catch (e) {
      erreur = e instanceof Error ? e.message : "Erreur lors de l'analyse";
    } finally {
      enCours = false;
    }
  }
</script>

<div class="fr-container fr-py-4w">
  <div class="fr-grid-row fr-grid-row--middle fr-mb-3w">
    <div class="fr-col">
      <h1 class="fr-h2">Correspondance de fonctionnalités</h1>
    </div>
    <div class="fr-col-auto">
      <button
        class="fr-btn fr-btn--secondary"
        type="button"
        disabled={enCours}
        onclick={analyser}
      >
        {enCours ? 'Analyse…' : 'Analyser les correspondances'}
      </button>
    </div>
  </div>

  {#if erreur}
    <div class="fr-alert fr-alert--error fr-mb-3w">
      <p>{erreur}</p>
    </div>
  {/if}

  {#if !analyse}
    <p class="fr-text--lg">
      Lancez l'analyse pour regrouper les fonctionnalités proches issues des
      transcripts et de FeatureBase, classées par nombre d'occurrences.
    </p>
  {:else if clusters.length === 0}
    <p class="fr-text--lg">Aucune fonctionnalité à rapprocher.</p>
  {:else}
    <div class="fr-table fr-table--bordered">
      <table>
        <thead>
          <tr>
            <th scope="col">Fonctionnalité</th>
            <th scope="col" class="col-occ">Occurrences</th>
          </tr>
        </thead>
        <tbody>
          {#each clusters as cluster (cluster.libelle)}
            <tr>
              <td>
                <details>
                  <summary>{cluster.libelle}</summary>
                  <ul class="fr-mt-1w membres-liste">
                    {#each cluster.membres as membre (membre.source + membre.texte)}
                      {@const cle = membre.source + membre.texte}
                      {@const sourceLabel =
                        membre.source === 'transcript'
                          ? 'Transcript'
                          : membre.source === 'idee'
                            ? 'Fonctionnalité'
                            : 'Retour BizDev'}
                      <li class="membre-ligne">
                        <span class="fr-badge fr-badge--sm fr-badge--no-icon"
                          >{sourceLabel}</span
                        >
                        {#if membre.source === 'transcript' && membre.transcript_id !== null}
                          <button
                            class="lien-transcript fr-btn fr-btn--tertiary-no-outline fr-btn--sm"
                            type="button"
                            onclick={() =>
                              onnaviquer({
                                nom: 'transcripts:detail',
                                id: membre.transcript_id!,
                              })}>transcript #{membre.transcript_id}</button
                          >
                        {/if}
                        {membre.texte}
                        {#if membre.verbatim}
                          <button
                            class="fr-btn fr-btn--tertiary-no-outline fr-btn--sm btn-verbatim"
                            type="button"
                            onclick={() => toggleVerbatim(cle)}
                            >{verbatimsOuverts.has(cle)
                              ? 'Masquer verbatim'
                              : 'Afficher verbatim'}</button
                          >
                          {#if verbatimsOuverts.has(cle)}
                            <span class="verbatim-texte">« {membre.verbatim} »</span>
                          {/if}
                        {/if}
                      </li>
                    {/each}
                  </ul>
                </details>
              </td>
              <td class="col-occ">
                <span class="fr-badge fr-badge--info">{cluster.occurrences}</span>
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  {/if}
</div>

<style>
  .col-occ {
    width: 8rem;
    text-align: center;
  }
  .membres-liste li {
    margin: 0.4rem 0;
  }
  .membre-ligne {
    display: flex;
    align-items: baseline;
    flex-wrap: wrap;
    gap: 0.4rem;
  }
  .lien-transcript {
    font-size: 0.75rem;
    color: var(--blue-france-sun-113-625, #000091);
    text-decoration: underline;
    padding: 0;
  }
  .btn-verbatim {
    font-size: 0.75rem;
    color: var(--blue-france-sun-113-625, #000091);
    padding: 0;
  }
  .verbatim-texte {
    display: block;
    width: 100%;
    margin-top: 0.2rem;
    padding-left: 1rem;
    font-style: italic;
    color: var(--text-mention-grey, #666);
    font-size: 0.875rem;
  }
</style>
