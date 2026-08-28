<script lang="ts">
  import { creerProjet, type Produit } from '../api/projets';
  import Contenu from './Contenu.svelte';

  let { produit, oncree }: { produit: Produit; oncree: (id: number) => void } =
    $props();
  let nom = $state('');
  let brief = $state('');
  let erreur = $state('');
  let enCours = $state(false);

  async function enregistrer() {
    enCours = true;
    erreur = '';
    try {
      const projet = await creerProjet({ produit_id: produit.id, nom, brief });
      oncree(projet.id);
    } catch (e) {
      erreur =
        e instanceof Error ? e.message : 'Erreur lors de la création du projet';
    } finally {
      enCours = false;
    }
  }
</script>

<Contenu largeur="32rem">
  <h1>Créer un projet de recherche</h1>
  <label>Nom du projet de recherche<input class="fr-input" bind:value={nom} /></label
  >
  <label
    >Brief de recherche<textarea class="fr-input" bind:value={brief}
    ></textarea></label
  >
  {#if erreur}<p class="erreur">{erreur}</p>{/if}
  <button class="fr-btn" disabled={enCours} onclick={enregistrer}
    >{enCours ? 'Création…' : 'Créer le projet'}</button
  >
</Contenu>

<style>
  h1 {
    font-size: clamp(2rem, 3vw, 2.7rem);
    margin: 4rem 0 2rem;
  }
  label {
    display: block;
    margin: 1.5rem 0;
    max-width: var(--largeur-saisie, 32rem);
  }
  input,
  textarea {
    display: block;
    margin-top: 0.5rem;
  }
  textarea {
    min-height: 8rem;
  }
  button {
    margin-top: 1.5rem;
  }
  .erreur {
    color: #ce0500;
  }
</style>
