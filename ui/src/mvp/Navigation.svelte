<script lang="ts">
  let { produitId, vue }: { produitId: number; vue: 'dashboard' | 'projets' } =
    $props();
</script>

<nav>
  <a class:actif={vue === 'dashboard'} href={`#/produits/${produitId}/dashboard`}
    >Dashboard</a
  ><a class:actif={vue === 'projets'} href={`#/produits/${produitId}/projets`}
    >Projets</a
  >
</nav>

<style>
  nav {
    border-bottom: 1px solid var(--border-default-grey);
    box-shadow: 0 2px 3px rgb(0 0 0 / 7%);
    display: flex;
    gap: 3rem;
    padding: 1rem max(1.5rem, calc((100% - 1200px) / 2));
  }
  a {
    background: none;
    color: var(--text-title-grey);
    text-decoration: none;
  }
  .actif {
    box-shadow: inset 0 -2px var(--border-action-high-blue-france);
    font-weight: 700;
  }
</style>
