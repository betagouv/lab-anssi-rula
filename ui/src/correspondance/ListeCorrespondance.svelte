<script lang="ts">
  import { SvelteSet } from 'svelte/reactivity';
  import type { Cluster, Membre } from '../types';
  import {
    chargerCorrespondances,
    analyserCorrespondances,
  } from '../api/correspondances';
  import { hashDepuisVue } from '../navigation/routage';
  import { cleCluster, cleMembre } from './cles';

  function lienSource(membre: Membre): string | null {
    if (membre.source === 'transcript' && membre.transcript_id !== null) {
      return hashDepuisVue({
        nom: 'sources:entretiens:detail',
        id: membre.transcript_id,
      });
    }
    if (membre.source === 'retour_bizdev' && membre.source_id !== null) {
      return hashDepuisVue({
        nom: 'sources:retours-bizdev:detail',
        id: membre.source_id,
      });
    }
    if (membre.source === 'idee' && membre.source_id !== null) {
      return hashDepuisVue({
        nom: 'sources:featurebase:detail',
        id: membre.source_id,
      });
    }
    return null;
  }

  let clusters = $state<Cluster[]>([]);
  let analyse = $state(false);
  let enCours = $state(false);
  let erreur = $state<string | null>(null);
  const verbatimsOuverts = new SvelteSet<string>();

  $effect(() => {
    chargerCorrespondances()
      .then((data) => {
        if (data.length > 0) {
          clusters = data;
          analyse = true;
        }
      })
      .catch((e) => {
        erreur = e instanceof Error ? e.message : 'Erreur lors du chargement';
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
      <h1 class="fr-h2">Correspondances</h1>
      <p class="fr-text--sm fr-mb-0">
        Vue unifiée des besoins génériques issus des entretiens, de FeatureBase et de
        BizDev, rapprochés par embeddings.
      </p>
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
  {:else if !analyse}
    <p class="fr-text--lg">
      Lancez l'analyse pour rapprocher les noms génériques issus des trois sources.
      Les verbatims restent consultables pour comprendre chaque rapprochement.
    </p>
  {:else if clusters.length === 0}
    <p class="fr-text--lg">Aucune demande à rapprocher.</p>
  {:else}
    <div class="fr-table fr-table--bordered">
      <table>
        <thead>
          <tr>
            <th scope="col">Demande rapprochée</th>
            <th scope="col" class="col-occ">Occurrences</th>
          </tr>
        </thead>
        <tbody>
          {#each clusters as cluster, clusterIndex (cleCluster(cluster, clusterIndex))}
            <tr>
              <td>
                <details>
                  <summary>{cluster.libelle}</summary>
                  <ul class="fr-mt-1w membres-liste">
                    {#each cluster.membres as membre, membreIndex (cleMembre(membre, membreIndex))}
                      {@const cle = cleMembre(membre, membreIndex)}
                      {@const sourceLabel =
                        membre.source === 'transcript'
                          ? 'Entretien'
                          : membre.source === 'idee'
                            ? 'FeatureBase'
                            : 'BizDev'}
                      {@const sourceLien = lienSource(membre)}
                      <li class="membre-ligne">
                        <span class="fr-badge fr-badge--sm fr-badge--no-icon"
                          >{sourceLabel}</span
                        >
                        {#if sourceLien}
                          <a
                            class="lien-source fr-btn fr-btn--tertiary-no-outline fr-btn--sm"
                            href={sourceLien}>Voir la source</a
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
  .lien-source {
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
