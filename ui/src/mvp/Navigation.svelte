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
    box-shadow:
      inset 0 1px var(--border-default-grey, #ddd),
      0 2px 3px rgb(0 0 18 / 16%);
    box-sizing: border-box;
    display: flex;
    gap: 1.5rem;
    height: 3.5rem;
    padding: 0 max(1.5rem, calc((100% - 1200px) / 2));
  }
  a {
    align-items: center;
    background: none;
    color: var(--text-action-high-grey, #161616);
    display: flex;
    line-height: 1.5rem;
    padding: 1rem 0.75rem 1rem 1rem;
    position: relative;
    text-decoration: none;
  }
  a:first-child {
    padding-left: 0;
    padding-right: 1rem;
  }
  .actif {
    color: var(--text-action-high-blue-france, #000091);
  }
  .actif::after {
    background: var(--border-action-high-blue-france, #000091);
    bottom: 0;
    content: '';
    height: 2px;
    left: 0;
    position: absolute;
    right: 0;
  }
  a:first-child.actif::after {
    left: -1rem;
  }
</style>
