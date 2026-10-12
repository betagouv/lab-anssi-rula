<script lang="ts">
  type Remplacement = {
    valeur_originale: string;
    valeur_anonyme: string;
    categorie: string;
    champ: string;
  };

  let { remplacements }: { remplacements: Remplacement[] } = $props();
</script>

{#if remplacements.length}
  <h2>Remplacements proposés</h2>
  <table>
    <thead
      ><tr
        ><th>Champ</th><th>Valeur détectée</th><th>Remplacement</th><th>Catégorie</th
        ></tr
      ></thead
    >
    <tbody>
      {#each remplacements as remplacement, index (index)}
        <tr
          ><td>{remplacement.champ === 'transcript' ? 'Transcript' : 'Contexte'}</td
          ><td>{remplacement.valeur_originale}</td><td
            >{remplacement.valeur_anonyme}</td
          ><td>{remplacement.categorie}</td></tr
        >
      {/each}
    </tbody>
  </table>
{/if}
