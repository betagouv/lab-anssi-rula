<script lang="ts">
  import type { Produit } from '../api/projets';

  let {
    produits,
    prefixe,
    produitId = $bindable(''),
    confirmation = $bindable(false),
    onchange,
  }: {
    produits: Produit[];
    prefixe: string;
    produitId: string;
    confirmation: boolean;
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
  <div class="fr-col-12 fr-col-md-8 fr-pl-md-2w">
    <div class="fr-checkbox-group fr-mt-4w">
      <input
        id={`confirmation-${prefixe}`}
        type="checkbox"
        bind:checked={confirmation}
      />
      <label class="fr-label" for={`confirmation-${prefixe}`}>
        Je confirme que l’import est autorisé et ne contient pas de donnée non
        conforme.
      </label>
    </div>
  </div>
</div>
