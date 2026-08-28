<script lang="ts">
  import { marked } from 'marked';
  import {
    genererEtapeAnalyse,
    modifierEtapeAnalyse,
    obtenirConfigurationAnalyse,
    validerEtapeAnalyse,
    type EtapeAnalyse as Etape,
    type Projet,
  } from '../api/projets';
  import ProgressionAnalyse from './ProgressionAnalyse.svelte';

  let {
    projet,
    cle,
    onvalide,
  }: { projet: Projet; cle: string; onvalide: () => void } = $props();
  let etape = $state<Etape | null>(null);
  let contenu = $state('');
  let erreur = $state('');
  let enCours = $state(false);
  const courant = $derived(etape ? etape.ordre : 3);

  $effect(() => {
    obtenirConfigurationAnalyse(projet.id)
      .then((configuration) => {
        etape = configuration.etapes.find((item) => item.cle === cle) ?? null;
        contenu = etape?.brouillon ?? '';
        if (!etape) erreur = 'Étape introuvable.';
      })
      .catch(
        (e) => (erreur = e instanceof Error ? e.message : 'Erreur de chargement')
      );
  });

  async function lancer() {
    enCours = true;
    erreur = '';
    try {
      etape = await genererEtapeAnalyse(projet.id, cle);
      contenu = etape.brouillon ?? '';
    } catch (e) {
      erreur = e instanceof Error ? e.message : 'Erreur de génération';
    } finally {
      enCours = false;
    }
  }

  async function valider() {
    enCours = true;
    erreur = '';
    try {
      await modifierEtapeAnalyse(projet.id, cle, contenu);
      await validerEtapeAnalyse(projet.id, cle);
      onvalide();
    } catch (e) {
      erreur = e instanceof Error ? e.message : 'Erreur de validation';
    } finally {
      enCours = false;
    }
  }
</script>

<main class="contenu">
  <ProgressionAnalyse {courant} />
  <h1>{etape?.ordre ?? courant} - {etape?.libelle ?? 'Analyse'}</h1>
  {#if erreur}<p class="erreur" role="alert">{erreur}</p>{/if}
  {#if contenu}
    <article>
      <!-- eslint-disable-next-line svelte/no-at-html-tags -->
      {@html marked.parse(contenu)}
    </article>
    <label>Je corrige<textarea bind:value={contenu}></textarea></label>
    <button class="fr-btn" disabled={enCours} onclick={valider}
      >{enCours ? 'Validation…' : 'Je passe à l’étape suivante'}</button
    >
    <button class="secondaire" disabled={enCours} onclick={lancer}
      >Régénérer l’étape</button
    >
  {:else}
    <button class="fr-btn" disabled={enCours} onclick={lancer}
      >{enCours ? 'Analyse…' : 'Générer cette étape'}</button
    >
  {/if}
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
    margin: 3.5rem 0 2rem;
  }
  article {
    line-height: 1.5;
    max-width: 61rem;
  }
  article :global(h2),
  article :global(h3) {
    margin: 1.5rem 0 0.75rem;
  }
  article :global(table) {
    border-collapse: collapse;
    display: block;
    max-width: 100%;
    overflow-x: auto;
    width: max-content;
  }
  article :global(th),
  article :global(td) {
    border: 1px solid var(--border-default-grey);
    padding: 0.75rem 1rem;
    text-align: left;
  }
  label {
    display: block;
    margin: 3rem 0 1.5rem;
    max-width: 61rem;
  }
  textarea {
    background: var(--background-alt-grey);
    border: 0;
    border-bottom: 2px solid var(--border-plain-grey);
    box-sizing: border-box;
    display: block;
    margin-top: 0.5rem;
    min-height: 8rem;
    padding: 1rem;
    resize: vertical;
    width: 100%;
  }
  .erreur {
    color: var(--text-default-error);
  }
  .secondaire {
    background: none;
    border: 0;
    color: var(--text-action-high-blue-france);
    margin-left: 1rem;
    padding: 0.75rem 0;
  }
</style>
