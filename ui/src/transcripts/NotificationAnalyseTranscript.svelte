<script lang="ts">
  let {
    statut,
    voirAnalyse,
  }: { statut: 'prete' | 'echec'; voirAnalyse: () => void } = $props();
</script>

<section class="notification" aria-label="État de l’analyse">
  <p role="status">
    {statut === 'prete'
      ? 'Analyse terminée. Consultez l’onglet « Analyse générée » pour voir le résultat.'
      : 'L’analyse a échoué. Consultez l’onglet « Analyse générée » pour voir le message et réessayer.'}
  </p>
  <button class="fr-btn fr-btn--secondary" type="button" onclick={voirAnalyse}
    >{statut === 'prete' ? 'Voir l’analyse' : 'Voir l’erreur'}</button
  >
</section>

<style>
  .notification {
    align-items: center;
    background: var(--background-alt-blue-france);
    display: flex;
    flex-wrap: wrap;
    gap: 0 1rem;
    justify-content: space-between;
    margin-top: 1rem;
    padding: 1rem;
  }
  .notification p {
    margin: 0.25rem 0;
  }
</style>
