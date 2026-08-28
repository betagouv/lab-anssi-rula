<script lang="ts">
  import type { Snippet } from 'svelte';

  let { largeur = '68rem', children }: { largeur?: string; children?: Snippet } =
    $props();
</script>

<main class="contenu" style={`--largeur-saisie: ${largeur}`}>
  {@render children?.()}
</main>

<style>
  .contenu {
    box-sizing: border-box;
    margin: 3.5rem auto;
    max-width: 1200px;
    padding: 0;
    width: calc(100% - 3rem);
  }
</style>
