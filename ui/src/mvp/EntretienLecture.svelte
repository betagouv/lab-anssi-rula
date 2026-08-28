<script lang="ts">
  import { obtenirEntretien, type Entretien, type Projet } from '../api/projets';
  import Contenu from './Contenu.svelte';

  let { projet, entretienId }: { projet: Projet; entretienId: number } = $props();
  let entretien = $state<Entretien | null>(null);
  let erreur = $state('');

  $effect(() => {
    obtenirEntretien(projet.id, entretienId)
      .then((valeur) => (entretien = valeur))
      .catch(
        (e) => (erreur = e instanceof Error ? e.message : 'Erreur de chargement')
      );
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
    <h2>Transcript brut</h2>
    <pre>{entretien.contenu}</pre>
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
