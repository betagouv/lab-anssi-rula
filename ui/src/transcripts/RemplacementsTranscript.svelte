<script lang="ts">
  type Remplacement = {
    valeur_originale: string;
    valeur_anonyme: string;
    categorie: string;
    champ: string;
  };

  let {
    remplacements,
    conflitsCategoriesFusionnes = 0,
  }: { remplacements: Remplacement[]; conflitsCategoriesFusionnes?: number } =
    $props();
</script>

{#if conflitsCategoriesFusionnes > 0}
  <div class="fr-alert fr-alert--warning" role="status">
    <p>
      {conflitsCategoriesFusionnes === 1
        ? 'Une zone de chevauchement a été fusionnée'
        : `${conflitsCategoriesFusionnes} zones de chevauchement ont été fusionnées`} en
      catégorie « donnée sensible ». Des mots voisins peuvent être anonymisés en plus :
      relisez le brouillon avant de le confirmer.
    </p>
  </div>
{/if}
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
