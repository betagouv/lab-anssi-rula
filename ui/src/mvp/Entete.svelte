<script lang="ts">
  let { produit = undefined }: { produit?: string } = $props();
</script>

<header class="entete">
  <a class="marque" href="#/" aria-label="Rula, accueil">
    <span class="fr-logo">République<br />Française</span>
    <img class="anssi" src="/anssi.svg" alt="ANSSI" />
    <span class="titre"
      ><strong>Rula</strong>{#if produit}
        <b>{produit}</b>{/if}<small>Analyse des retours utilisateurs</small></span
    >
  </a>
</header>

<style>
  .entete {
    box-shadow: 0 2px 4px rgb(0 0 0 / 16%);
    padding: 1.5rem max(1.5rem, calc((100% - 1200px) / 2));
  }
  .marque {
    align-items: center;
    background: none;
    color: var(--text-title-grey);
    display: flex;
    gap: 1.25rem;
    text-decoration: none;
  }
  .marque:focus-visible {
    outline: 2px solid var(--border-action-high-blue-france);
    outline-offset: 0.25rem;
  }
  .fr-logo {
    flex: 0 0 auto;
    zoom: 0.75;
  }
  .anssi {
    height: 3.75rem;
    width: 3.75rem;
  }
  strong {
    font-size: 1.25rem;
  }
  b {
    background: var(--background-contrast-success);
    color: var(--text-default-success);
    font-size: 0.7rem;
    margin-left: 0.5rem;
    padding: 0.25rem;
  }
  small {
    color: var(--text-default-grey);
    display: block;
    margin-top: 0.35rem;
  }
</style>
