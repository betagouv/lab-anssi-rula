<script lang="ts">
  import {
    creerEntretien,
    genererScan,
    listerEntretiens,
    ProjetNonConforme,
    type RaisonRefusProjet,
    type Entretien,
    type Projet,
  } from '../api/projets';
  import Contenu from './Contenu.svelte';
  import FormulaireEntretien from './FormulaireEntretien.svelte';
  import Guide from './Guide.svelte';
  import Progression from './Progression.svelte';
  import ResultatGardeFou from './ResultatGardeFou.svelte';
  let { projet, onscan }: { projet: Projet; onscan: () => void } = $props();
  let entretiens = $state<Entretien[]>([]);
  let ouvert = $state(false);
  let confirmation = $state(false);
  let participant = $state('');
  let date_entretien = $state('');
  let moderateur = $state('');
  let contenu = $state('');
  let note_moderateur = $state('');
  let erreur = $state('');
  let raisons = $state<RaisonRefusProjet[]>([]);
  let enCours = $state(false);
  $effect(() => {
    listerEntretiens(projet.id)
      .then((v) => (entretiens = v))
      .catch((e) => (erreur = e.message));
  });
  async function ajouter() {
    if (!confirmation) {
      raisons = [];
      erreur = 'Confirmez la préparation des données avant de les enregistrer.';
      return;
    }
    enCours = true;
    erreur = '';
    raisons = [];
    try {
      entretiens = [
        ...entretiens,
        await creerEntretien(projet.id, {
          participant,
          date_entretien,
          moderateur,
          contenu,
          note_moderateur,
          confirmation,
        }),
      ];
      ouvert = false;
      confirmation = false;
      participant = date_entretien = moderateur = contenu = note_moderateur = '';
    } catch (e) {
      if (e instanceof ProjetNonConforme) raisons = e.raisons;
      else erreur = e instanceof Error ? e.message : 'Erreur';
    } finally {
      enCours = false;
    }
  }
  async function scanner() {
    enCours = true;
    erreur = '';
    try {
      await genererScan(projet.id);
      onscan();
    } catch (e) {
      erreur = e instanceof Error ? e.message : 'Erreur';
    } finally {
      enCours = false;
    }
  }
</script>

<Contenu>
  <Progression courant={1} suivante="Scanner les données" />
  <h2>Importer vos données brutes</h2>
  <h1>{projet.nom}</h1>
  {#if projet.brief}<section>
      <h2>Brief</h2>
      <p>{projet.brief}</p>
    </section>{/if}
  <h2>Les entretiens</h2>
  <div class="tableau">
    <table>
      <thead
        ><tr
          ><th>Titre</th><th>Date</th><th>Répondant</th><th>Donnée brute</th><th
            >Commentaires</th
          ><th>Interviewer</th></tr
        ></thead
      ><tbody
        >{#each entretiens as entretien (entretien.id)}<tr
            ><td>Entretien {entretien.id}</td><td>{entretien.date_entretien}</td><td
              >{entretien.participant}</td
            ><td>Transcript</td><td>{entretien.note_moderateur ? 'Oui' : 'Non'}</td
            ><td>{entretien.moderateur}</td></tr
          >{/each}</tbody
      >
    </table>
  </div>
  <button class="fr-btn fr-btn--secondary" onclick={() => (ouvert = true)}
    >+ Ajouter un entretien</button
  >{#if erreur}<p class="erreur">{erreur}</p>{/if}<button
    class="fr-btn"
    disabled={!entretiens.length || enCours}
    onclick={scanner}>{enCours ? 'Analyse…' : 'Lancer l’analyse'}</button
  >
</Contenu>

{#if ouvert}<div class="fond" role="presentation">
    <dialog class="modale" open aria-modal="true" aria-label="Ajouter un entretien">
      <button class="fermer" onclick={() => (ouvert = false)}>Fermer ×</button>
      <h1>→ Ajouter un entretien</h1>
      <FormulaireEntretien
        bind:participant
        bind:date_entretien
        bind:moderateur
        bind:contenu
        bind:note_moderateur
        compact
      /><Guide bind:confirme={confirmation} /><ResultatGardeFou {raisons} />
      {#if erreur}<p class="erreur">{erreur}</p>{/if}
      <div class="actions">
        <button class="fr-btn" disabled={enCours} onclick={ajouter}
          >{enCours ? 'Vérification…' : 'Enregistrer'}</button
        ><button class="annuler" onclick={() => (ouvert = false)}>Annuler</button>
      </div>
    </dialog>
  </div>{/if}

<style>
  h1 {
    font-size: clamp(2rem, 3vw, 2.7rem);
    margin: 3.5rem 0 2rem;
  }
  .tableau {
    overflow-x: auto;
    margin-bottom: 2rem;
  }
  table {
    border-collapse: collapse;
    min-width: 56rem;
  }
  th,
  td {
    border-bottom: 1px solid var(--border-default-grey);
    padding: 1rem;
    text-align: left;
  }
  th {
    background: var(--background-alt-grey);
  }
  .erreur {
    color: #ce0500;
  }
  .fond {
    align-items: start;
    background: rgb(0 0 0 / 28%);
    display: flex;
    inset: 0;
    justify-content: center;
    overflow: auto;
    padding: 5rem 1rem;
    position: fixed;
    z-index: 2;
  }
  .modale {
    background: var(--background-default-grey);
    border: 0;
    box-shadow: 0 2px 12px rgb(0 0 0 / 28%);
    max-width: 48rem;
    padding: 2rem;
    width: 100%;
    --largeur-saisie: 30rem;
  }
  .modale h1 {
    font-size: 1.6rem;
    margin: 2rem 0 1rem;
  }
  .fermer {
    background: none;
    border: 0;
    color: var(--text-action-high-blue-france);
    float: right;
  }
  .annuler {
    background: none;
    border: 0;
    color: var(--text-action-high-blue-france);
  }
  .actions {
    align-items: center;
    display: flex;
    gap: 1.5rem;
    margin-top: 1.5rem;
  }
</style>
