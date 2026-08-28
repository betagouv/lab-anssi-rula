<script lang="ts">
  import type { Produit } from '../api/projets';
  let { produits }: { produits: Produit[] } = $props();
</script>

<main class="entree">
  {#each [...produits].reverse() as produit (produit.id)}
    <a href={`#/produits/${produit.id}/dashboard`} class="carte">
      <img
        class="picto"
        src={produit.nom === 'MSS'
          ? '/pictogramme-ville.svg'
          : '/pictogramme-maison.svg'}
        alt=""
      /><b>LIBELLÉ</b>
      <h1>{produit.nom}</h1>
    </a>
  {/each}
</main>

<style>
  .entree {
    box-sizing: border-box;
    display: grid;
    gap: 1.5rem;
    grid-template-columns: repeat(auto-fit, minmax(min(100%, 20rem), 1fr));
    margin: 9rem auto;
    max-width: 1200px;
    padding: 0;
    width: calc(100% - 3rem);
  }
  .carte {
    border: 1px solid var(--border-default-grey);
    border-bottom: 4px solid var(--border-plain-grey);
    color: var(--text-title-grey);
    display: grid;
    justify-items: center;
    height: 19.25rem;
    min-height: 0;
    padding: 2rem;
    text-align: center;
    text-decoration: none;
  }
  .picto {
    height: 5rem;
    width: 6rem;
  }
  b {
    background: var(--background-contrast-pink-macaron);
    color: #6e445a;
    font-size: 0.7rem;
    padding: 0.35rem;
  }
  h1 {
    margin: 0.75rem 0 0;
  }
</style>
