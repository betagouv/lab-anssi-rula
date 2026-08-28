<script lang="ts">
  import {
    ajouterSource,
    listerProjets,
    ProjetNonConforme,
    type Produit,
    type Projet,
    type RaisonRefusProjet,
  } from '../api/projets';
  import { importerIdeesProjet } from '../api/idees';
  import { importerRetoursProjet } from '../api/retours_bizdev';
  import Contenu from './Contenu.svelte';
  import FormulaireEntretien from './FormulaireEntretien.svelte';
  import Guide from './Guide.svelte';
  import ResultatGardeFou from './ResultatGardeFou.svelte';

  type Source = 'transcript' | 'bizdev' | 'featurebase';
  const NOUVEAU = '__nouveau__';
  const TITRES: Record<Source, string> = {
    transcript: 'Ajouter un transcript',
    bizdev: 'Importer des entretiens BizDev',
    featurebase: 'Importer des demandes FeatureBase',
  };
  let {
    produit,
    source,
    projetInitialId = null,
  }: {
    produit: Produit;
    source: Source;
    projetInitialId?: number | null;
  } = $props();
  let projets = $state<Projet[]>([]);
  let projetId = $state('');
  let nom = $state('');
  let brief = $state('');
  let fichier = $state<File | null>(null);
  let participant = $state('');
  let date_entretien = $state('');
  let moderateur = $state('');
  let contenu = $state('');
  let note_moderateur = $state('');
  let confirmation = $state(false);
  let raisons = $state<RaisonRefusProjet[]>([]);
  let erreur = $state('');
  let resultat = $state('');
  let projetCible = $state<number | null>(null);
  let enCours = $state(false);
  let ouvert = $state(false);

  $effect(() => {
    if (projetInitialId && !projetId) projetId = String(projetInitialId);
  });

  $effect(() => {
    listerProjets(produit.id)
      .then((valeurs) => (projets = valeurs))
      .catch(
        (e) => (erreur = e instanceof Error ? e.message : 'Erreur de chargement')
      );
  });

  function selection() {
    return projetId === NOUVEAU
      ? { nouveau_projet: { nom, brief } }
      : { projet_id: Number(projetId) };
  }

  function changerProjet() {
    erreur = '';
    raisons = [];
    resultat = '';
    projetCible = null;
  }

  function changerFichier(event: Event) {
    fichier = (event.currentTarget as HTMLInputElement).files?.[0] ?? null;
    erreur = '';
    resultat = '';
  }

  async function enregistrer() {
    erreur = '';
    raisons = [];
    resultat = '';
    projetCible = null;
    if (!projetId) {
      erreur = 'Sélectionnez un projet ou créez-en un nouveau.';
      return;
    }
    if (source === 'transcript' && !confirmation) {
      erreur = 'Confirmez la préparation du transcript avant de l’enregistrer.';
      return;
    }
    if (source !== 'transcript' && !fichier) {
      erreur = 'Sélectionnez un fichier CSV à importer.';
      return;
    }
    if (source !== 'transcript' && !confirmation) {
      erreur = 'Confirmez l’autorisation de l’import avant de continuer.';
      return;
    }
    enCours = true;
    try {
      if (source === 'transcript') {
        const reponse = await ajouterSource(produit.id, {
          ...selection(),
          entretien: {
            participant,
            date_entretien,
            moderateur,
            contenu,
            note_moderateur,
          },
          confirmation,
        });
        projetCible = reponse.projet.id;
        resultat = 'Le transcript a été ajouté au projet.';
        ouvert = false;
        window.location.hash = `#/projets/${reponse.projet.id}/configuration`;
      } else {
        const reponse =
          source === 'bizdev'
            ? await importerRetoursProjet(
                fichier!,
                produit.id,
                selection(),
                confirmation
              )
            : await importerIdeesProjet(
                fichier!,
                produit.id,
                selection(),
                confirmation
              );
        projetCible = reponse.projet.id;
        resultat = `${reponse.sources.length} élément(s) importé(s) dans le projet.`;
      }
    } catch (e) {
      if (e instanceof ProjetNonConforme) raisons = e.raisons;
      else
        erreur = e instanceof Error ? e.message : 'Erreur lors de l’enregistrement';
    } finally {
      enCours = false;
    }
  }

  function ouvrirEntretien() {
    erreur = '';
    raisons = [];
    ouvert = true;
  }
</script>

<Contenu largeur="40rem">
  <a href={`#/produits/${produit.id}/projets`}>← Projets</a>
  <p>Produit : <strong>{produit.nom}</strong></p>
  <h1>{TITRES[source]}</h1>

  <label
    >Projet de recherche<select
      class="fr-select"
      value={projetId}
      onchange={(event) => {
        projetId = (event.currentTarget as HTMLSelectElement).value;
        changerProjet();
      }}
      ><option value="">Sélectionner un projet</option><option value={NOUVEAU}
        >Créer un nouveau projet</option
      >{#each projets as projet (projet.id)}<option value={String(projet.id)}
          >{projet.nom}</option
        >{/each}</select
    ></label
  >

  {#if projetId === NOUVEAU}
    <label
      >Nom du projet de recherche<input class="fr-input" bind:value={nom} /></label
    >
    <label
      >Brief de recherche<textarea class="fr-input" bind:value={brief}
      ></textarea></label
    >
  {/if}

  {#if source === 'transcript'}
    <button
      class="fr-btn fr-btn--secondary"
      disabled={!projetId}
      onclick={ouvrirEntretien}>+ Ajouter un entretien</button
    >
  {:else}
    <label
      >Fichier CSV<input
        type="file"
        accept=".csv"
        onchange={changerFichier}
      /></label
    >
    <label class="confirmation"
      ><input type="checkbox" bind:checked={confirmation} /> Je confirme que l’import est
      autorisé et ne contient pas de donnée non conforme.</label
    >
  {/if}

  {#if erreur}<p class="erreur">{erreur}</p>{/if}
  {#if resultat}<p class="succes">{resultat}</p>{/if}
  {#if projetCible}<a href={`#/projets/${projetCible}`}>Voir le projet cible</a>{/if}
  {#if source !== 'transcript'}<button
      class="fr-btn"
      disabled={enCours}
      onclick={enregistrer}>{enCours ? 'Vérification…' : 'Importer'}</button
    >{/if}
</Contenu>

{#if ouvert}
  <div class="fond" role="presentation">
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
      />
      <Guide bind:confirme={confirmation} />
      <ResultatGardeFou {raisons} />
      {#if erreur}<p class="erreur">{erreur}</p>{/if}
      <div class="actions">
        <button class="fr-btn" disabled={enCours} onclick={enregistrer}
          >{enCours ? 'Vérification…' : 'Enregistrer'}</button
        >
        <button class="annuler" onclick={() => (ouvert = false)}>Annuler</button>
      </div>
    </dialog>
  </div>
{/if}

<style>
  h1 {
    font-size: clamp(2rem, 3vw, 2.7rem);
    margin: 3rem 0 2rem;
  }
  label {
    display: block;
    margin: 1.5rem 0;
    max-width: var(--largeur-saisie, 40rem);
  }
  input,
  textarea,
  select {
    display: block;
    margin-top: 0.5rem;
  }
  textarea {
    min-height: 8rem;
  }
  label.confirmation {
    align-items: start;
    display: flex;
    gap: 0.5rem;
  }
  label.confirmation input {
    margin-top: 0.2rem;
  }
  button {
    margin-top: 1.5rem;
  }
  .erreur {
    color: #ce0500;
  }
  .succes {
    color: #18753c;
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
