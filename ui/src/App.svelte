<script lang="ts">
  import type { Vue } from './types';
  import NavigationPrincipale from './navigation/NavigationPrincipale.svelte';
  import ListeTranscripts from './transcripts/ListeTranscripts.svelte';
  import FormulaireTranscript from './transcripts/FormulaireTranscript.svelte';
  import DetailTranscript from './transcripts/DetailTranscript.svelte';
  import ListeAnalyses from './analyses/ListeAnalyses.svelte';

  let vue = $state<Vue>({ nom: 'transcripts:liste' });

  function naviguer(v: Vue) {
    vue = v;
  }
</script>

<NavigationPrincipale {vue} onnaviquer={naviguer} />

<main>
  {#if vue.nom === 'transcripts:liste'}
    <ListeTranscripts onnaviquer={naviguer} />
  {:else if vue.nom === 'transcripts:ajout'}
    <FormulaireTranscript onnaviquer={naviguer} />
  {:else if vue.nom === 'transcripts:detail'}
    <DetailTranscript id={vue.id} onnaviquer={naviguer} />
  {:else if vue.nom === 'transcripts:modification'}
    <FormulaireTranscript id={vue.id} onnaviquer={naviguer} />
  {:else if vue.nom === 'analyses'}
    <ListeAnalyses onnaviquer={naviguer} />
  {/if}
</main>
