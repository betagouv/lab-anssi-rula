<script lang="ts">
  import { onMount } from 'svelte';
  import TranscriptPseudonymise from './TranscriptPseudonymise.svelte';
  import {
    nomPseudonymise,
    obtenirTranscriptPdf,
    type TranscriptPdf,
  } from './pseudonymiser_api';

  let {
    transcriptId,
    produitNom,
    retour,
  }: {
    transcriptId: number;
    produitNom: string;
    retour: () => void;
  } = $props();
  let transcript = $state<TranscriptPdf | null>(null);
  let erreur = $state('');

  onMount(() => {
    obtenirTranscriptPdf(transcriptId)
      .then((valeur) => (transcript = valeur))
      .catch(
        (cause) =>
          (erreur =
            cause instanceof Error ? cause.message : 'Transcript introuvable.')
      );
  });
</script>

<main class="page">
  <button
    class="fr-btn fr-btn--tertiary-no-outline fr-icon-arrow-left-line fr-btn--icon-left retour"
    type="button"
    onclick={retour}>Retour aux transcripts importés</button
  >
  {#if erreur}<p role="alert">{erreur}</p>
  {:else if !transcript}<p role="status" aria-live="polite">
      Chargement du transcript…
    </p>
  {:else}
    <div class="titre">
      <div>
        <p class="fr-text--sm">
          {produitNom} · {transcript.type_source === 'bizdev'
            ? 'Retour BizDev'
            : 'Entretien utilisateur'}
        </p>
        <h1>{nomPseudonymise(transcript.nom_source)}</h1>
        <p>Date de l’entretien : {transcript.date_entretien ?? 'Non renseignée'}</p>
      </div>
      <a
        class="fr-btn fr-btn--secondary"
        href={`/api/transcripts-pdf/${transcript.id}/pdf`}
        download={nomPseudonymise(transcript.nom_source)}>Télécharger le PDF</a
      >
    </div>
    {#if transcript.contexte}<section>
        <h2>Contexte</h2>
        <p class="texte">{transcript.contexte}</p>
      </section>{/if}
    <section>
      <h2>Transcript pseudonymisé</h2>
      <TranscriptPseudonymise contenu={transcript.contenu} />
    </section>
    {#if transcript.locuteurs.length}<section>
        <h2>Locuteurs</h2>
        <ul>
          {#each transcript.locuteurs as locuteur (locuteur.identifiant)}<li>
              {locuteur.nom_affiche || locuteur.identifiant} — {locuteur.role}
            </li>{/each}
        </ul>
      </section>{/if}
  {/if}
</main>

<style>
  .page {
    max-width: 1032px;
    margin: 0 auto;
    padding: 32px 16px 80px;
  }
  .retour {
    margin-bottom: 24px;
  }
  .titre {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: space-between;
    gap: 20px;
    margin-bottom: 32px;
  }
  h1 {
    overflow-wrap: anywhere;
  }
  h2 {
    margin-bottom: 12px;
    font-size: 22px;
  }
  section {
    margin-block: 24px;
  }
  .texte {
    white-space: pre-wrap;
    overflow-wrap: anywhere;
  }
</style>
