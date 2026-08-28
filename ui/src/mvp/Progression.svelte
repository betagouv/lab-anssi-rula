<script lang="ts">
  let {
    courant,
    suivante,
    total = 3,
  }: { courant: number; suivante: string; total?: number } = $props();
</script>

<p>Étape {courant} sur {total}</p>
<div class="progression" aria-label={`Étape ${courant} sur ${total}`}>
  {#each Array.from({ length: total }, (_, index) => index) as index (index)}
    <i class:active={index + 1 === courant}></i>
  {/each}
</div>
<p>Étape suivante : {suivante}</p>

<style>
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
  i.active {
    background: var(--background-action-high-blue-france);
  }
</style>
