<script lang="ts">
  import { onMount } from 'svelte';
  import type { Vue } from './types';
  import NavigationPrincipale from './navigation/NavigationPrincipale.svelte';
  import ListeTranscripts from './transcripts/ListeTranscripts.svelte';
  import FormulaireTranscript from './transcripts/FormulaireTranscript.svelte';
  import DetailTranscript from './transcripts/DetailTranscript.svelte';
  import ListeAnalyses from './analyses/ListeAnalyses.svelte';
  import ListeFonctionnalites from './fonctionnalites/ListeFonctionnalites.svelte';
  import ListeCorrespondance from './correspondance/ListeCorrespondance.svelte';
  import ListeRetoursBizDev from './retours/ListeRetoursBizDev.svelte';
  import ListeBesoinsDetectes from './besoins/ListeBesoinsDetectes.svelte';
  import { hashDepuisVue, vueDepuisHash } from './navigation/routage';

  let vue = $state<Vue>(vueDepuisHash(''));

  function naviguer(v: Vue) {
    const hash = hashDepuisVue(v);
    if (window.location.hash === hash) {
      vue = v;
    } else {
      window.location.hash = hash;
    }
  }

  onMount(() => {
    const synchroniser = () => {
      vue = vueDepuisHash(window.location.hash);
    };

    if (!window.location.hash) {
      window.history.replaceState(null, '', hashDepuisVue(vue));
    } else {
      synchroniser();
    }

    window.addEventListener('hashchange', synchroniser);
    return () => window.removeEventListener('hashchange', synchroniser);
  });
</script>

<NavigationPrincipale {vue} />

<main>
  {#if vue.nom === 'sources:entretiens'}
    <ListeTranscripts onnaviquer={naviguer} />
  {:else if vue.nom === 'sources:entretiens:ajout'}
    <FormulaireTranscript onnaviquer={naviguer} />
  {:else if vue.nom === 'sources:entretiens:detail'}
    <DetailTranscript id={vue.id} onnaviquer={naviguer} />
  {:else if vue.nom === 'sources:entretiens:modification'}
    <FormulaireTranscript id={vue.id} onnaviquer={naviguer} />
  {:else if vue.nom === 'analyses'}
    <ListeAnalyses />
  {:else if vue.nom === 'besoins'}
    <ListeBesoinsDetectes />
  {:else if vue.nom === 'sources:featurebase'}
    <ListeFonctionnalites />
  {:else if vue.nom === 'sources:retours-bizdev'}
    <ListeRetoursBizDev />
  {:else if vue.nom === 'correspondances'}
    <ListeCorrespondance />
  {/if}
</main>
