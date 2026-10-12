<script lang="ts">
  import {
    obtenirAnalyseTranscriptPdf,
    type AnalyseTranscriptPdf,
  } from '../api/transcripts_pdf';
  import { obtenirEntretien, type Entretien, type Projet } from '../api/projets';
  import ResultatAnalyse from '../transcripts/ResultatAnalyse.svelte';
  import Contenu from './Contenu.svelte';

  let { projet, entretienId }: { projet: Projet; entretienId: number } = $props();
  let entretien = $state<Entretien | null>(null);
  let analyse = $state<AnalyseTranscriptPdf | null>(null);
  let erreur = $state('');
  let erreurAnalyse = $state('');
  let chargementAnalyse = $state(true);
  let ongletActif = $state<'analyse' | 'transcript'>('analyse');

  $effect(() => {
    obtenirEntretien(projet.id, entretienId)
      .then((valeur) => (entretien = valeur))
      .catch(
        (e) => (erreur = e instanceof Error ? e.message : 'Erreur de chargement')
      );
    obtenirAnalyseTranscriptPdf(entretienId)
      .then((valeur) => (analyse = valeur))
      .catch(
        (e) =>
          (erreurAnalyse = e instanceof Error ? e.message : 'Erreur de chargement')
      )
      .finally(() => (chargementAnalyse = false));
  });
</script>

<Contenu largeur="61rem">
  <a href={`#/projets/${projet.id}`}>← Retour au projet</a>
  {#if erreur}
    <p class="erreur" role="alert">{erreur}</p>
  {:else if entretien}
    <h1>Entretien {entretien.id}</h1>
    <dl>
      <div>
        <dt>Participant</dt>
        <dd>{entretien.participant}</dd>
      </div>
      <div>
        <dt>Date de l’entretien</dt>
        <dd>{entretien.date_entretien}</dd>
      </div>
      <div>
        <dt>Modérateur</dt>
        <dd>{entretien.moderateur}</dd>
      </div>
      <div>
        <dt>Note du modérateur</dt>
        <dd>{entretien.note_moderateur || 'Aucune'}</dd>
      </div>
    </dl>
    <div class="onglets" role="tablist" aria-label="Contenu de l’entretien">
      <button
        id="onglet-analyse"
        class:actif={ongletActif === 'analyse'}
        role="tab"
        aria-selected={ongletActif === 'analyse'}
        aria-controls="panneau-analyse"
        tabindex={ongletActif === 'analyse' ? 0 : -1}
        onclick={() => (ongletActif = 'analyse')}
        onkeydown={(event) => {
          if (event.key === 'ArrowRight') {
            ongletActif = 'transcript';
            document.getElementById('onglet-transcript')?.focus();
          }
        }}>Analyse générée</button
      >
      <button
        id="onglet-transcript"
        class:actif={ongletActif === 'transcript'}
        role="tab"
        aria-selected={ongletActif === 'transcript'}
        aria-controls="panneau-transcript"
        tabindex={ongletActif === 'transcript' ? 0 : -1}
        onclick={() => (ongletActif = 'transcript')}
        onkeydown={(event) => {
          if (event.key === 'ArrowLeft') {
            ongletActif = 'analyse';
            document.getElementById('onglet-analyse')?.focus();
          }
        }}>Transcript brut</button
      >
    </div>
    <div
      id="panneau-analyse"
      role="tabpanel"
      aria-labelledby="onglet-analyse"
      hidden={ongletActif !== 'analyse'}
    >
      {#if chargementAnalyse}
        <p>Chargement de l’analyse…</p>
      {:else if erreurAnalyse}
        <p class="erreur" role="alert">{erreurAnalyse}</p>
      {:else if analyse}
        <ResultatAnalyse contenu={analyse.contenu} />
      {:else}
        <p>Aucune analyse générée pour cet entretien.</p>
      {/if}
    </div>
    <div
      id="panneau-transcript"
      role="tabpanel"
      aria-labelledby="onglet-transcript"
      hidden={ongletActif !== 'transcript'}
    >
      <h2>Transcript brut</h2>
      <pre>{entretien.contenu}</pre>
    </div>
  {:else}
    <p>Chargement…</p>
  {/if}
</Contenu>

<style>
  h1 {
    font-size: clamp(2rem, 3vw, 2.7rem);
    margin: 3rem 0 2rem;
  }
  dl {
    display: grid;
    gap: 1rem;
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  dt {
    font-weight: 700;
  }
  dd {
    margin: 0.25rem 0 0;
  }
  h2 {
    margin-top: 3rem;
  }
  .onglets {
    border-bottom: 1px solid var(--border-default-grey);
    display: flex;
    gap: 1.5rem;
    margin-top: 3rem;
  }
  .onglets button {
    background: transparent;
    border: 0;
    border-bottom: 0.25rem solid transparent;
    color: var(--text-action-high-blue-france);
    cursor: pointer;
    font: inherit;
    padding: 0.75rem 0;
  }
  .onglets button.actif {
    border-color: var(--border-action-high-blue-france);
    font-weight: 700;
  }
  [role='tabpanel'] {
    margin-top: 1.5rem;
  }
  pre {
    background: var(--background-alt-grey);
    border-left: 0.25rem solid var(--border-default-grey);
    padding: 1.5rem;
    white-space: pre-wrap;
    overflow-wrap: anywhere;
  }
  a {
    color: var(--text-action-high-blue-france);
  }
  .erreur {
    color: var(--text-default-error);
  }
  @media (max-width: 48rem) {
    dl {
      grid-template-columns: 1fr;
    }
  }
</style>
