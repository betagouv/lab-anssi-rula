<script lang="ts">
  import ResultatAnalyse from './ResultatAnalyse.svelte';

  let {
    contenu,
    chargement,
    desactive,
    erreur,
    relancer,
    lancer,
  }: {
    contenu: Record<string, unknown> | null;
    chargement: boolean;
    desactive: boolean;
    erreur: string;
    relancer: boolean;
    lancer: () => void;
  } = $props();
</script>

<section aria-busy={chargement}>
  {#if chargement}
    <p class="statut" role="status">
      Analyse en cours… Le résultat apparaîtra ici dès qu’il sera prêt.
    </p>
  {:else if erreur}
    <p class="erreur" role="alert">{erreur}</p>
  {:else if contenu}
    <ResultatAnalyse {contenu} />
  {:else}
    <p>
      Après lancement, le résumé et les points clés de l’analyse apparaîtront ici.
    </p>
  {/if}
  {#if !contenu || relancer || erreur}
    <button
      class="fr-btn"
      type="button"
      disabled={desactive || chargement}
      onclick={lancer}
    >
      {#if chargement}<span class="indicateur" aria-hidden="true"></span>{/if}
      {chargement
        ? 'Analyse en cours…'
        : relancer
          ? 'Relancer l’analyse'
          : erreur
            ? 'Réessayer l’analyse'
            : 'Lancer l’analyse'}
    </button>
  {/if}
</section>

<style>
  .statut {
    margin: 1.5rem 0;
  }
  .erreur {
    color: var(--text-default-error);
  }
  .indicateur {
    animation: rotation 0.8s linear infinite;
    border: 0.15rem solid currentColor;
    border-radius: 50%;
    border-right-color: transparent;
    display: inline-block;
    height: 1rem;
    margin-right: 0.5rem;
    vertical-align: -0.15rem;
    width: 1rem;
  }
  @keyframes rotation {
    to {
      transform: rotate(360deg);
    }
  }
  @media (prefers-reduced-motion: reduce) {
    .indicateur {
      animation: none;
      border-right-color: currentColor;
    }
  }
</style>
