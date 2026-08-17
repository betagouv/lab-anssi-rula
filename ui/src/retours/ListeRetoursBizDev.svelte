<script lang="ts">
  import type { RetourBizDev } from '../types';
  import { importerRetours, listerRetours } from '../api/retours_bizdev';

  let retours = $state<RetourBizDev[]>([]);
  let chargement = $state(true);
  let enCours = $state(false);
  let erreur = $state<string | null>(null);

  $effect(() => {
    listerRetours()
      .then((data) => {
        retours = data;
      })
      .catch((e) => {
        erreur = e instanceof Error ? e.message : 'Erreur lors du chargement';
      })
      .finally(() => {
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
      retours = await importerRetours(fichier);
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
      <h1 class="fr-h2">Retours BizDev</h1>
      {#if !chargement}
        <p class="fr-text--sm fr-mb-0">{retours.length} retour(s)</p>
      {/if}
    </div>
    <div class="fr-col-auto">
      <label class="fr-btn fr-btn--secondary" for="import-retours-csv">
        {enCours ? 'Import…' : 'Importer un export BizDev'}
      </label>
      <input
        id="import-retours-csv"
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
  {:else if chargement}
    <p>Chargement…</p>
  {:else if retours.length === 0}
    <p class="fr-text--lg">
      Aucun retour importé. Cliquez sur "Importer un export BizDev" pour charger
      l'export.
    </p>
  {:else}
    <div class="fr-table fr-table--bordered">
      <table>
        <thead>
          <tr>
            <th scope="col">Verbatim</th>
            <th scope="col" class="col-meta">Catégorie</th>
            <th scope="col" class="col-meta">Item</th>
            <th scope="col" class="col-meta">Rôle</th>
            <th scope="col" class="col-meta">Qui</th>
            <th scope="col" class="col-meta">Date</th>
          </tr>
        </thead>
        <tbody>
          {#each retours as retour (retour.id)}
            <tr>
              <td>{retour.verbatim}</td>
              <td class="col-meta">{retour.categorie ?? ''}</td>
              <td class="col-meta">{retour.item ?? ''}</td>
              <td class="col-meta">{retour.role ?? ''}</td>
              <td class="col-meta">{retour.qui ?? ''}</td>
              <td class="col-meta">{retour.date_retour ?? ''}</td>
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

  .col-meta {
    width: 8rem;
    font-size: 0.875rem;
  }
</style>
