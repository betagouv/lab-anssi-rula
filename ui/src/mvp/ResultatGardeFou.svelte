<script lang="ts">
  import type { RaisonRefusProjet } from '../api/projets';

  let { raisons }: { raisons: RaisonRefusProjet[] } = $props();
</script>

{#if raisons.length}
  <section class="refus" role="alert">
    <h3>Transcript non enregistré</h3>
    <p>Corrigez les éléments signalés avant de réessayer.</p>
    <ul>
      {#each raisons as raison (raison.categorie + '-' + raison.element)}
        <li>{raison.element} : {raison.raison}</li>
      {/each}
    </ul>
  </section>
{/if}

<style>
  .refus {
    border-left: 0.25rem solid var(--border-plain-error, #ce0500);
    margin-top: 1.5rem;
    padding: 0.75rem 1rem;
  }
  h3 {
    margin: 0 0 0.5rem;
  }
  p {
    margin: 0 0 0.75rem;
  }
  ul {
    margin: 0;
  }
</style>
