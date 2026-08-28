<script lang="ts">
  import {
    genererEtapeAnalyse,
    modifierConfigurationAnalyse,
    obtenirConfigurationAnalyse,
    type BlocPrompt,
    type Projet,
  } from '../api/projets';
  import ProgressionAnalyse from './ProgressionAnalyse.svelte';

  let { projet, onlance }: { projet: Projet; onlance: () => void } = $props();
  let blocs = $state<BlocPrompt[]>([]);
  let erreur = $state('');
  let enCours = $state(false);

  $effect(() => {
    obtenirConfigurationAnalyse(projet.id)
      .then((configuration) => (blocs = configuration.blocs))
      .catch(
        (e) => (erreur = e instanceof Error ? e.message : 'Erreur de chargement')
      );
  });

  async function enregistrer() {
    enCours = true;
    erreur = '';
    try {
      await modifierConfigurationAnalyse(
        projet.id,
        Object.fromEntries(blocs.map((bloc) => [bloc.cle, bloc.contenu]))
      );
      await genererEtapeAnalyse(projet.id, 'scan-neutre');
      onlance();
    } catch (e) {
      erreur = e instanceof Error ? e.message : 'Erreur d’enregistrement';
    } finally {
      enCours = false;
    }
  }
</script>

<main class="contenu">
  <ProgressionAnalyse courant={2} />
  <h1>Configurez l’analyse</h1>
  <p>Personnalisez le prompt d’analyse</p>
  {#if erreur}<p class="erreur" role="alert">{erreur}</p>{/if}
  {#each blocs as bloc (bloc.cle)}
    <label>
      {bloc.libelle}
      <textarea
        bind:value={bloc.contenu}
        aria-label={bloc.libelle}
        class:long={bloc.cle !== 'role'}
      ></textarea>
    </label>
  {/each}
  <button class="fr-btn" disabled={enCours || !blocs.length} onclick={enregistrer}
    >{enCours ? 'Enregistrement…' : 'Lancer l’analyse'}</button
  >
</main>

<style>
  .contenu {
    box-sizing: border-box;
    margin: 3.5rem auto;
    max-width: 1200px;
    padding: 0;
    width: calc(100% - 3rem);
  }
  h1 {
    font-size: clamp(2rem, 3vw, 2.7rem);
    margin: 3.5rem 0 0.5rem;
  }
  label {
    display: block;
    margin: 1.5rem 0;
    max-width: 61rem;
  }
  textarea {
    background: var(--background-alt-grey);
    border: 0;
    border-bottom: 2px solid var(--border-plain-grey);
    box-sizing: border-box;
    display: block;
    margin-top: 0.5rem;
    min-height: 7rem;
    padding: 1rem;
    resize: vertical;
    width: 100%;
  }
  textarea:focus {
    outline: 2px solid var(--border-action-high-blue-france);
    outline-offset: 2px;
  }
  textarea.long {
    min-height: 13rem;
  }
  button {
    margin-top: 1rem;
  }
  .erreur {
    color: var(--text-default-error);
  }
</style>
