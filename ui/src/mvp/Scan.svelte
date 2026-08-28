<script lang="ts">
  import { marked } from 'marked';
  import {
    modifierScan,
    obtenirScan,
    validerScan,
    type Projet,
  } from '../api/projets';
  import Contenu from './Contenu.svelte';
  import Progression from './Progression.svelte';
  let { projet, onvalide }: { projet: Projet; onvalide: () => void } = $props();
  let contenu = $state('');
  let erreur = $state('');
  let enCours = $state(false);
  $effect(() => {
    obtenirScan(projet.id)
      .then((scan) => (contenu = scan.brouillon))
      .catch((e) => (erreur = e.message));
  });
  async function valider() {
    enCours = true;
    erreur = '';
    try {
      await modifierScan(projet.id, contenu);
      await validerScan(projet.id);
      onvalide();
    } catch (e) {
      erreur = e instanceof Error ? e.message : 'Erreur';
    } finally {
      enCours = false;
    }
  }
</script>

<Contenu>
  <Progression courant={2} suivante="Consulter l’analyse" />
  <h2>Scanner les données</h2>
  <h1>1 - Scan neutre des données</h1>
  {#if erreur}<p class="erreur">{erreur}</p>{:else}<article>
      <!-- eslint-disable-next-line svelte/no-at-html-tags -->
      {@html marked.parse(contenu)}
    </article>
    <label>Je corrige<textarea bind:value={contenu}></textarea></label><button
      class="fr-btn"
      disabled={enCours}
      onclick={valider}
      >{enCours ? 'Validation…' : 'Je passe à l’étape suivante'}</button
    >{/if}
</Contenu>

<style>
  h1 {
    font-size: clamp(2rem, 3vw, 2.7rem);
    margin: 3.5rem 0 2rem;
  }
  article {
    border: 0;
    box-sizing: border-box;
    font: inherit;
    line-height: 1.5;
    min-height: 22rem;
    padding: 0;
    width: min(100%, 68rem);
  }
  article :global(h2),
  article :global(h3) {
    margin: 1.5rem 0 0.75rem;
  }
  article :global(p) {
    margin: 0.75rem 0;
  }
  article :global(ul),
  article :global(ol) {
    padding-left: 1.5rem;
  }
  article :global(table) {
    border-collapse: collapse;
    display: block;
    margin: 1rem 0;
    max-width: 100%;
    overflow-x: auto;
    width: max-content;
  }
  article :global(th),
  article :global(td) {
    border: 1px solid var(--border-default-grey);
    padding: 0.75rem 1rem;
    text-align: left;
    vertical-align: top;
  }
  article :global(th) {
    background: var(--background-alt-grey);
  }
  label textarea {
    background: var(--background-alt-grey);
    border-bottom: 2px solid var(--border-plain-grey);
    display: block;
    margin-top: 0.5rem;
    min-height: 6rem;
    padding: 1rem;
  }
  label {
    display: block;
    margin: 3rem 0 1.5rem;
  }
  .erreur {
    color: #ce0500;
  }
</style>
