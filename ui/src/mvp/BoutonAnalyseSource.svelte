<script lang="ts">
  let { produitId }: { produitId: number } = $props();
</script>

<details class="menu">
  <summary class="fr-btn">Analyser une source de données</summary>
  <nav aria-label="Analyser une source de données">
    <a href={`#/produits/${produitId}/sources/transcript`}>Ajouter un transcript</a>
    <a href={`#/produits/${produitId}/sources/bizdev`}
      >Importer des entretiens BizDev</a
    >
    <a href={`#/produits/${produitId}/sources/featurebase`}
      >Importer des demandes FeatureBase</a
    >
  </nav>
</details>

<style>
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
</style>
