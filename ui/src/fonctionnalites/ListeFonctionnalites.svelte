<script lang="ts">
  import type { Idee } from '../types';
  import { listerIdees, synchroniserIdees } from '../api/idees';

  let idees = $state<Idee[]>([]);
  let chargement = $state(true);
  let enCours = $state(false);
  let erreur = $state<string | null>(null);

  $effect(() => {
    listerIdees().then((data) => {
      idees = data;
      chargement = false;
    });
  });

  async function synchroniser() {
    enCours = true;
    erreur = null;
    try {
      idees = await synchroniserIdees();
    } catch (e) {
      erreur = e instanceof Error ? e.message : 'Erreur lors de la synchronisation';
    } finally {
      enCours = false;
    }
  }
</script>

<div class="fr-container fr-py-4w">
  <div class="fr-grid-row fr-grid-row--middle fr-mb-3w">
    <div class="fr-col">
      <h1 class="fr-h2">Fonctionnalités</h1>
    </div>
    <div class="fr-col-auto">
      <button
        class="fr-btn fr-btn--secondary"
        type="button"
        disabled={enCours}
        onclick={synchroniser}
      >
        {enCours ? 'Synchronisation…' : 'Synchroniser FeatureBase'}
      </button>
    </div>
  </div>

  {#if erreur}
    <div class="fr-alert fr-alert--error fr-mb-3w">
      <p>{erreur}</p>
    </div>
  {/if}

  {#if chargement}
    <p>Chargement…</p>
  {:else if idees.length === 0}
    <p class="fr-text--lg">
      Aucune idée synchronisée. Cliquez sur "Synchroniser FeatureBase" pour importer
      les idées.
    </p>
  {:else}
    <div class="fr-table fr-table--bordered">
      <table>
        <thead>
          <tr>
            <th scope="col">Fonctionnalité</th>
            <th scope="col" class="col-votes">Votes</th>
          </tr>
        </thead>
        <tbody>
          {#each idees as idee (idee.id_externe)}
            <tr>
              <td>{idee.titre}</td>
              <td class="col-votes">
                <span class="fr-badge fr-badge--info">{idee.nb_votes}</span>
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  {/if}
</div>

<style>
  .col-votes {
    width: 6rem;
    text-align: center;
  }
</style>
