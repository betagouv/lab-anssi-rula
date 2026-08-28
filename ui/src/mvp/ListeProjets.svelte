<script lang="ts">
  import type { Produit, Projet } from '../api/projets';
  import Navigation from './Navigation.svelte';
  let { produit, projets }: { produit: Produit; projets: Projet[] } = $props();
</script>

<Navigation produitId={produit.id} vue="projets" />
<main class="contenu">
  <details class="menu">
    <summary class="fr-btn action">Ajouter une source de données</summary>
    <nav aria-label="Ajouter une source de données">
      <a href={`#/produits/${produit.id}/sources/transcript`}
        >Ajouter un transcript</a
      >
      <a href={`#/produits/${produit.id}/sources/bizdev`}
        >Importer des entretiens BizDev</a
      >
      <a href={`#/produits/${produit.id}/sources/featurebase`}
        >Importer des demandes FeatureBase</a
      >
    </nav>
  </details>
  <h1>Projets</h1>
  <div class="onglets">
    <span>Entretiens utilisateurs UX</span><span>Entretiens BizDev</span><span
      >CSV retours utilisateurs</span
    ><span>FeatureBase</span>
  </div>
  {#if projets.length}<div class="tableau">
      <table>
        <thead
          ><tr
            ><th>Nom du projet</th><th>Date de création</th><th>Créateur</th><th
              >Type</th
            ><th>Nombre de sources</th><th>Interviewer</th></tr
          ></thead
        ><tbody
          >{#each projets as projet (projet.id)}<tr
              ><td><a href={`#/projets/${projet.id}`}>{projet.nom}</a></td><td
                >{new Date(projet.cree_le).toLocaleDateString('fr-FR')}</td
              ><td>—</td><td>Entretien UX</td><td>—</td><td>—</td></tr
            >{/each}</tbody
        >
      </table>
    </div>{:else}<p>Aucun projet de recherche pour ce produit.</p>{/if}
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
    margin: 2rem 0;
  }
  .action {
    float: right;
  }
  .menu {
    float: right;
    position: relative;
  }
  .menu summary {
    cursor: pointer;
    list-style: none;
  }
  .menu summary::-webkit-details-marker {
    display: none;
  }
  .menu nav {
    background: var(--background-default-grey);
    border: 1px solid var(--border-default-grey);
    box-shadow: 0 2px 8px rgb(0 0 0 / 18%);
    display: grid;
    min-width: 19rem;
    position: absolute;
    right: 0;
    top: calc(100% + 0.5rem);
    z-index: 1;
  }
  .menu nav a {
    color: var(--text-action-high-blue-france);
    padding: 0.75rem 1rem;
    text-decoration: none;
  }
  .menu nav a:hover,
  .menu nav a:focus {
    background: var(--background-alt-blue-france);
  }
  .onglets {
    border: 1px solid var(--border-default-grey);
    display: flex;
    margin-bottom: 3.75rem;
    overflow-x: auto;
    width: fit-content;
    max-width: 100%;
  }
  .onglets span {
    padding: 0.75rem 1rem;
    white-space: nowrap;
  }
  .onglets span:first-child {
    border: 1px solid var(--border-action-high-blue-france);
    color: var(--text-action-high-blue-france);
  }
  .tableau {
    overflow-x: auto;
  }
  table {
    border-collapse: collapse;
    min-width: 48rem;
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
