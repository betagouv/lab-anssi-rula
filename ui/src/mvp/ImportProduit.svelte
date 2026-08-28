<script lang="ts">
  import type { Produit } from '../api/projets';

  let {
    produits,
    prefixe,
    produitId = $bindable(''),
    onchange,
  }: {
    produits: Produit[];
    prefixe: string;
    produitId: string;
    onchange: () => void;
  } = $props();
</script>

<div class="fr-grid-row fr-grid-row--middle fr-mb-3w">
  <div class="fr-col-12 fr-col-md-4">
    <label class="fr-label" for={`produit-${prefixe}`}>Produit</label>
    <select
      id={`produit-${prefixe}`}
      class="fr-select"
      bind:value={produitId}
      {onchange}
    >
      <option value="">Sélectionner un produit</option>
      {#each produits as produit (produit.id)}
        <option value={produit.id}>{produit.nom}</option>
      {/each}
    </select>
  </div>
</div>
