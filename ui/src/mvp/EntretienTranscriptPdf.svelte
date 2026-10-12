<script lang="ts">
  import {
    obtenirSourceTranscriptPdf,
    type SourceTranscriptPdf,
  } from '../api/transcripts_pdf';
  import { obtenirProjet, type Projet } from '../api/projets';
  import EntretienLecture from './EntretienLecture.svelte';
  import Contenu from './Contenu.svelte';

  let { produitId, transcriptId }: { produitId: number; transcriptId: number } =
    $props();
  let projet = $state<Projet | null>(null);
  let erreur = $state('');

  $effect(() => {
    obtenirSourceTranscriptPdf(transcriptId)
      .then((source: SourceTranscriptPdf) => {
        if (
          source.type_source !== 'produit' ||
          source.produit_id !== produitId ||
          !source.projet_id
        )
          throw new Error('Ce transcript produit est introuvable.');
        return obtenirProjet(source.projet_id);
      })
      .then((valeur) => (projet = valeur))
      .catch(
        (e) => (erreur = e instanceof Error ? e.message : 'Erreur de chargement')
      );
  });
</script>

{#if erreur}
  <Contenu><p class="erreur" role="alert">{erreur}</p></Contenu>
{:else if projet}
  <EntretienLecture {projet} entretienId={transcriptId} />
{:else}
  <Contenu><p>Chargement du transcript…</p></Contenu>
{/if}

<style>
  .erreur {
    color: var(--text-default-error);
  }
</style>
