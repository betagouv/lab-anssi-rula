<script lang="ts">
  import type { Produit, Projet } from '../api/projets';
  import Navigation from './Navigation.svelte';
  let { produit, projets }: { produit: Produit; projets: Projet[] } = $props();
</script>

<Navigation produitId={produit.id} vue="dashboard" />
<main class="contenu">
  <a href={`#/produits/${produit.id}/projets`} class="fr-btn action"
    >Analyser une source de données</a
  >
  <h1>Dashboard {produit.nom}</h1>
  {#if projets.length}
    <table>
      <thead><tr><th>Projet de recherche</th><th>État</th></tr></thead><tbody
        >{#each projets as projet (projet.id)}<tr
            ><td><a href={`#/projets/${projet.id}`}>{projet.nom}</a></td><td
              >À analyser</td
            ></tr
          >{/each}</tbody
      >
    </table>
  {:else}<p>
      Aucune demande à rapprocher. Ajoutez un projet de recherche pour commencer.
    </p>{/if}
</main>

<style>
  .contenu {
    box-sizing: border-box;
    margin: 2.5rem auto;
    max-width: 1200px;
    padding: 0;
    width: calc(100% - 3rem);
  }
  h1 {
    font-size: clamp(2rem, 3vw, 2.7rem);
    margin: 2rem 0 4rem;
  }
  .action {
    float: right;
  }
  table {
    border-collapse: collapse;
    max-width: 48rem;
    width: 100%;
  }
  th,
  td {
    border-bottom: 1px solid var(--border-default-grey);
    padding: 1rem;
    text-align: left;
  }
  th {
    background: var(--background-alt-grey);
  }
  td a {
    color: var(--text-action-high-blue-france);
  }
</style>
