<script lang="ts">
  import type { Idee } from '../types';
  import { listerIdees } from '../api/idees';

  let { id }: { id: number } = $props();
  let idee = $state<Idee | null>(null);
  let chargement = $state(true);
  let erreur = $state<string | null>(null);

  $effect(() => {
    listerIdees()
      .then((idees) => {
        idee = idees.find((item) => item.id === id) ?? null;
        if (!idee) erreur = 'Cette demande FeatureBase est introuvable.';
      })
      .catch((e) => {
        erreur = e instanceof Error ? e.message : 'Erreur lors du chargement';
      })
      .finally(() => {
        chargement = false;
      });
  });
</script>

<div class="fr-container fr-py-4w">
  <nav class="fr-breadcrumb" aria-label="vous êtes ici :">
    <ol class="fr-breadcrumb__list">
      <li>
        <a class="fr-breadcrumb__link" href="#sources/featurebase"
          >Demandes FeatureBase</a
        >
      </li>
      <li><span aria-current="page">Détail de la demande #{id}</span></li>
    </ol>
  </nav>

  <h1 class="fr-h2">Demande FeatureBase #{id}</h1>

  {#if chargement}
    <p>Chargement…</p>
  {:else if erreur}
    <div class="fr-alert fr-alert--error">
      <p>{erreur}</p>
    </div>
  {:else if idee}
    <dl class="fr-grid-row fr-grid-row--gutters">
      <div class="fr-col-12">
        <dt class="fr-text--bold">Donnée brute</dt>
        <dd class="donnee-brute">{idee.titre}</dd>
      </div>
      <div class="fr-col-12 fr-col-md-6">
        <dt class="fr-text--bold">Votes</dt>
        <dd>{idee.nb_votes}</dd>
      </div>
      <div class="fr-col-12 fr-col-md-6">
        <dt class="fr-text--bold">Importée le</dt>
        <dd>{idee.importe_le}</dd>
      </div>
    </dl>
  {/if}
</div>

<style>
  .donnee-brute {
    white-space: pre-wrap;
  }
</style>
