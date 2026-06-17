<script lang="ts">
  import type { Idee } from '../types';
  import { importerIdees, listerIdees } from '../api/idees';

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

  async function handleFichier(event: Event) {
    const input = event.target as HTMLInputElement;
    const fichier = input.files?.[0];
    if (!fichier) return;
    enCours = true;
    erreur = null;
    try {
      idees = await importerIdees(fichier);
    } catch (e) {
      erreur = e instanceof Error ? e.message : "Erreur lors de l'import";
    } finally {
      enCours = false;
      input.value = '';
    }
  }
</script>

<div class="fr-container fr-py-4w">
  <div class="fr-grid-row fr-grid-row--middle fr-mb-3w">
    <div class="fr-col">
      <h1 class="fr-h2">Fonctionnalités</h1>
    </div>
    <div class="fr-col-auto">
      <label class="fr-btn fr-btn--secondary" for="import-csv">
        {enCours ? 'Import…' : 'Importer CSV FeatureBase'}
      </label>
      <input
        id="import-csv"
        type="file"
        accept=".csv"
        disabled={enCours}
        onchange={handleFichier}
        class="sr-only"
      />
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
      Aucune idée importée. Cliquez sur "Importer CSV FeatureBase" pour charger
      l'export.
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
          {#each idees as idee (idee.id)}
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
  .sr-only {
    position: absolute;
    width: 1px;
    height: 1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    white-space: nowrap;
  }

  .col-votes {
    width: 6rem;
    text-align: center;
  }
</style>
