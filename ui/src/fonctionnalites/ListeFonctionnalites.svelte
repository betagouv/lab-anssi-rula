<script lang="ts">
  import type { Idee } from '../types';
  import { importerIdees, listerIdees } from '../api/idees';
  import { listerProduits, type Produit } from '../api/projets';
  import { hashDepuisVue } from '../navigation/routage';
  import ImportProduit from '../mvp/ImportProduit.svelte';

  let { produitInitialId = null }: { produitInitialId?: number | null } = $props();
  let idees = $state<Idee[]>([]);
  let chargement = $state(true);
  let enCours = $state(false);
  let erreur = $state<string | null>(null);
  let produits = $state<Produit[]>([]);
  let produitId = $state('');

  $effect(() => {
    if (produitInitialId && !produitId) produitId = String(produitInitialId);
  });

  $effect(() => {
    listerProduits()
      .then((data) => {
        produits = data;
        if (produitInitialId) void charger();
      })
      .catch((e) => {
        erreur = e instanceof Error ? e.message : 'Erreur lors du chargement';
      })
      .finally(() => {
        chargement = false;
      });
  });

  async function charger() {
    if (!produitId) return;
    chargement = true;
    erreur = null;
    try {
      idees = await listerIdees(Number(produitId));
    } catch (e) {
      erreur = e instanceof Error ? e.message : 'Erreur lors du chargement';
    } finally {
      chargement = false;
    }
  }

  async function handleFichier(event: Event) {
    const input = event.target as HTMLInputElement;
    const fichier = input.files?.[0];
    if (!fichier) return;
    enCours = true;
    erreur = null;
    try {
      idees = await importerIdees(fichier, Number(produitId));
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
      <h1 class="fr-h2">Demandes FeatureBase</h1>
      {#if !chargement}
        <p class="fr-text--sm fr-mb-0">{idees.length} demande(s)</p>
      {/if}
    </div>
    <div class="fr-col-auto">
      <label class="fr-btn fr-btn--secondary" for="import-csv">
        {enCours ? 'Import…' : 'Importer un export FeatureBase'}
      </label>
      <input
        id="import-csv"
        type="file"
        accept=".csv"
        disabled={enCours || !produitId}
        onchange={handleFichier}
        class="sr-only"
      />
    </div>
  </div>
  {#if !produitInitialId}
    <ImportProduit
      {produits}
      prefixe="featurebase"
      bind:produitId
      onchange={charger}
    />
  {/if}

  {#if erreur}
    <div class="fr-alert fr-alert--error fr-mb-3w">
      <p>{erreur}</p>
    </div>
  {:else if chargement}
    <p>Chargement…</p>
  {:else if idees.length === 0}
    <p class="fr-text--lg">
      Aucune demande importée. Cliquez sur "Importer un export FeatureBase" pour
      charger l'export.
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
              <td>
                <a
                  class="lien-ligne"
                  href={hashDepuisVue({
                    nom: 'sources:featurebase:detail',
                    id: idee.id,
                  })}
                  aria-label={`Voir le détail de la demande FeatureBase #${idee.id}`}
                  >{idee.titre}</a
                >
              </td>
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

  .lien-ligne {
    display: block;
    color: inherit;
    text-decoration: none;
  }

  .lien-ligne:hover,
  .lien-ligne:focus {
    text-decoration: underline;
  }
</style>
