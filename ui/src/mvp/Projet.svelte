<script lang="ts">
  import {
    creerEntretien,
    listerEntretiens,
    obtenirConfigurationAnalyse,
    ProjetNonConforme,
    type RaisonRefusProjet,
    type Entretien,
    type EtapeAnalyse,
    type Projet,
  } from '../api/projets';
  import Contenu from './Contenu.svelte';
  import FormulaireEntretien from './FormulaireEntretien.svelte';
  import Guide from './Guide.svelte';
  import ResultatGardeFou from './ResultatGardeFou.svelte';
  let { projet, produitNom }: { projet: Projet; produitNom?: string } = $props();
  let entretiens = $state<Entretien[]>([]);
  let etapes = $state<EtapeAnalyse[]>([]);
  let chargement = $state(true);
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
    Promise.all([
      listerEntretiens(projet.id),
      obtenirConfigurationAnalyse(projet.id),
    ])
      .then(([entretiensProjet, configuration]) => {
        entretiens = entretiensProjet;
        etapes = configuration.etapes;
      })
      .catch(
        (e) => (erreur = e instanceof Error ? e.message : 'Erreur de chargement')
      )
      .finally(() => (chargement = false));
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
      window.location.hash = `#/projets/${projet.id}/configuration`;
    } catch (e) {
      if (e instanceof ProjetNonConforme) raisons = e.raisons;
      else erreur = e instanceof Error ? e.message : 'Erreur';
    } finally {
      enCours = false;
    }
  }
  function statut(etape: EtapeAnalyse) {
    return etape.statut === 'validee'
      ? 'Validée'
      : etape.statut === 'brouillon'
        ? 'Brouillon'
        : 'À faire';
  }
</script>

<Contenu>
  <div class="entete-projet">
    <div>
      <a href={'#/produits/' + projet.produit_id + '/projets'}>← Projets</a>
      <p>Produit : <strong>{produitNom ?? projet.produit_id}</strong></p>
    </div>
    <details class="menu">
      <summary class="fr-btn">Ajouter des données</summary>
      <nav aria-label="Ajouter des données au projet">
        <button class="menu-lien" type="button" onclick={() => (ouvert = true)}
          >Ajouter un transcript</button
        >
        <a href={'#/projets/' + projet.id + '/sources/bizdev'}
          >Importer des entretiens BizDev</a
        >
        <a href={'#/projets/' + projet.id + '/sources/featurebase'}
          >Importer des demandes FeatureBase</a
        >
      </nav>
    </details>
  </div>

  <h1>{projet.nom}</h1>
  {#if projet.brief}<section class="brief">
      <h2>Brief</h2>
      <p>{projet.brief}</p>
    </section>{/if}

  {#if erreur}<p class="erreur" role="alert">{erreur}</p>{/if}
  {#if chargement}<p>Chargement des données du projet…</p>{:else}
    <section>
      <h2>Entretiens utilisateurs</h2>
      {#if entretiens.length}<div class="tableau">
          <table>
            <thead
              ><tr
                ><th>Titre</th><th>Date</th><th>Répondant</th><th>Donnée brute</th
                ><th>Commentaires</th><th>Interviewer</th></tr
              ></thead
            ><tbody
              >{#each entretiens as entretien (entretien.id)}<tr
                  ><td
                    ><a
                      href={'#/projets/' + projet.id + '/entretiens/' + entretien.id}
                      >Entretien {entretien.id}</a
                    ></td
                  ><td>{entretien.date_entretien}</td><td>{entretien.participant}</td
                  ><td>Transcript</td><td
                    >{entretien.note_moderateur ? 'Oui' : 'Non'}</td
                  ><td>{entretien.moderateur}</td></tr
                >{/each}</tbody
            >
          </table>
        </div>{:else}<p class="vide">Aucun transcript rattaché à ce projet.</p>{/if}
    </section>

    <section>
      <h2>Données produit</h2>
      <p class="vide">
        Les retours BizDev et les demandes FeatureBase sont analysés au niveau du
        produit.
      </p>
      <a href={'#/produits/' + projet.produit_id + '/dashboard'}
        >Consulter l’analyse transverse du produit</a
      >
    </section>

    <section>
      <div class="titre-section">
        <h2>Analyses</h2>
        <a
          class="fr-btn fr-btn--secondary"
          href={'#/projets/' + projet.id + '/configuration'}>Configurer l’analyse</a
        >
      </div>
      {#if etapes.length}<ul class="analyses">
          {#each etapes as etape (etape.cle)}<li>
              <a href={'#/projets/' + projet.id + '/analyse/' + etape.cle}
                >{etape.libelle}</a
              >
              <span class:validee={etape.statut === 'validee'}>{statut(etape)}</span>
            </li>{/each}
        </ul>
        {#if etapes.some((etape) => etape.statut === 'validee')}<a
            href={'#/projets/' + projet.id + '/detail'}
            >Consulter le détail de l’analyse</a
          >{/if}{:else}<p class="vide">
          Aucune analyse configurée pour ce projet.
        </p>{/if}
    </section>
  {/if}
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
  .entete-projet,
  .titre-section {
    align-items: start;
    display: flex;
    gap: 1.5rem;
    justify-content: space-between;
  }
  .entete-projet a,
  section > a,
  td a,
  .analyses a {
    color: var(--text-action-high-blue-france);
  }
  .entete-projet p {
    margin-bottom: 0;
  }
  h1 {
    font-size: clamp(2rem, 3vw, 2.7rem);
    margin: 3.5rem 0 2rem;
  }
  h2 {
    margin-top: 2.5rem;
  }
  .brief {
    border-left: 0.25rem solid var(--border-default-grey);
    padding-left: 1rem;
  }
  section {
    margin-top: 3rem;
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
  .menu {
    position: relative;
  }
  .menu summary {
    cursor: pointer;
    list-style: none;
  }
  .menu summary::-webkit-details-marker {
    display: none;
  }
  .menu nav {
    background: var(--background-default-grey);
    border: 1px solid var(--border-default-grey);
    box-shadow: 0 2px 8px rgb(0 0 0 / 18%);
    display: grid;
    min-width: 20rem;
    position: absolute;
    right: 0;
    top: calc(100% + 0.5rem);
    z-index: 1;
  }
  .menu nav a,
  .menu-lien {
    background: none;
    border: 0;
    color: var(--text-action-high-blue-france);
    font: inherit;
    padding: 0.75rem 1rem;
    text-align: left;
    text-decoration: none;
  }
  .menu nav a:hover,
  .menu nav a:focus,
  .menu-lien:hover,
  .menu-lien:focus {
    background: var(--background-alt-blue-france);
  }
  .analyses {
    list-style: none;
    margin: 0 0 1rem;
    padding: 0;
  }
  .analyses li {
    align-items: center;
    border-bottom: 1px solid var(--border-default-grey);
    display: flex;
    gap: 1rem;
    justify-content: space-between;
    padding: 1rem 0;
  }
  .analyses span {
    background: var(--background-alt-grey);
    padding: 0.25rem 0.5rem;
  }
  .analyses span.validee {
    background: var(--background-contrast-success);
  }
  .vide {
    color: var(--text-mention-grey, #666);
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
  @media (max-width: 48rem) {
    .entete-projet,
    .titre-section,
    .analyses li {
      align-items: stretch;
      flex-direction: column;
    }
    .menu nav {
      left: 0;
      right: auto;
    }
  }
</style>
