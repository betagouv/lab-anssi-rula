<script lang="ts">
  import type { RetourBizDev } from '../types';
  import { listerRetours } from '../api/retours_bizdev';

  let { id }: { id: number } = $props();
  let retour = $state<RetourBizDev | null>(null);
  let chargement = $state(true);
  let erreur = $state<string | null>(null);

  $effect(() => {
    listerRetours()
      .then((retours) => {
        retour = retours.find((item) => item.id === id) ?? null;
        if (!retour) erreur = 'Ce retour BizDev est introuvable.';
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
        <a class="fr-breadcrumb__link" href="#sources/retours-bizdev"
          >Retours BizDev</a
        >
      </li>
      <li><span aria-current="page">Détail du retour #{id}</span></li>
    </ol>
  </nav>

  <h1 class="fr-h2">Retour BizDev #{id}</h1>

  {#if chargement}
    <p>Chargement…</p>
  {:else if erreur}
    <div class="fr-alert fr-alert--error">
      <p>{erreur}</p>
    </div>
  {:else if retour}
    <dl class="fr-grid-row fr-grid-row--gutters">
      <div class="fr-col-12">
        <dt class="fr-text--bold">Verbatim</dt>
        <dd class="verbatim">{retour.verbatim}</dd>
      </div>
      <div class="fr-col-12 fr-col-md-6">
        <dt class="fr-text--bold">Catégorie</dt>
        <dd>{retour.categorie ?? '—'}</dd>
      </div>
      <div class="fr-col-12 fr-col-md-6">
        <dt class="fr-text--bold">Item</dt>
        <dd>{retour.item ?? '—'}</dd>
      </div>
      <div class="fr-col-12 fr-col-md-6">
        <dt class="fr-text--bold">Rôle</dt>
        <dd>{retour.role ?? '—'}</dd>
      </div>
      <div class="fr-col-12 fr-col-md-6">
        <dt class="fr-text--bold">Qui</dt>
        <dd>{retour.qui ?? '—'}</dd>
      </div>
      <div class="fr-col-12 fr-col-md-6">
        <dt class="fr-text--bold">Date du retour</dt>
        <dd>{retour.date_retour ?? '—'}</dd>
      </div>
    </dl>
  {/if}
</div>

<style>
  .verbatim {
    white-space: pre-wrap;
  }
</style>
