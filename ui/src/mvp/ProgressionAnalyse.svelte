<script lang="ts">
  let { courant }: { courant: number } = $props();
  const etapes = [
    'Importer les données brutes',
    'Configurer l’analyse',
    'Scan neutre',
    'Points à retenir',
    'Thématisation',
    'Consulter l’analyse',
  ];
</script>

<p>Étape {courant} sur {etapes.length}</p>
<div class="progression" aria-label={`Étape ${courant} sur ${etapes.length}`}>
  {#each etapes as etape, index (etape)}
    <i class:active={index + 1 === courant} class:done={index + 1 < courant}></i>
  {/each}
</div>
<p class="suivante">
  {#if courant < etapes.length}Étape suivante : {etapes[courant]}{:else}Analyse
    consultable{/if}
</p>

<style>
  p {
    margin: 0 0 0.5rem;
  }
  .progression {
    display: flex;
    gap: 0.5rem;
    max-width: 36rem;
  }
  i {
    background: var(--background-alt-grey);
    height: 0.5rem;
    flex: 1;
  }
  i.active,
  i.done {
    background: var(--background-action-high-blue-france);
  }
  .suivante {
    margin-top: 0.25rem;
  }
</style>
