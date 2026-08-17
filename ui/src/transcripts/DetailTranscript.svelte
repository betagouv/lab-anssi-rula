<script lang="ts">
  import { marked } from 'marked';
  import type { Vue, Transcript, Analyse } from '../types';
  import { obtenirTranscript, supprimerTranscript } from '../api/transcripts';
  import { obtenirAnalyse, genererAnalyse } from '../api/analyses';

  let { id, onnaviquer }: { id: number; onnaviquer: (v: Vue) => void } = $props();

  type Ressource = { id: number; nom: string };

  let transcript = $state<Transcript | null>(null);
  let identiteNom = $state('');
  let produitNom = $state('');
  let confirmerSuppression = $state(false);
  let dialog = $state<HTMLDialogElement | null>(null);
  let erreur = $state<string | null>(null);

  let analyse = $state<Analyse | null>(null);
  let analyseChargee = $state(false);
  let analyseEnCours = $state(false);

  $effect(() => {
    Promise.all([
      obtenirTranscript(id),
      fetch('/api/identites').then((r) => r.json() as Promise<Ressource[]>),
      fetch('/api/produits').then((r) => r.json() as Promise<Ressource[]>),
    ])
      .then(([t, ids, prods]) => {
        transcript = t;
        identiteNom =
          ids.find((i) => i.id === t.identite_id)?.nom ?? String(t.identite_id);
        produitNom =
          prods.find((p) => p.id === t.produit_id)?.nom ?? String(t.produit_id);
      })
      .catch((e) => {
        erreur = e instanceof Error ? e.message : 'Erreur lors du chargement';
      });
  });

  $effect(() => {
    obtenirAnalyse(id)
      .then((a) => {
        analyse = a;
      })
      .catch((e) => {
        erreur =
          e instanceof Error ? e.message : "Erreur lors du chargement de l'analyse";
      })
      .finally(() => {
        analyseChargee = true;
      });
  });

  $effect(() => {
    if (!dialog) return;
    if (confirmerSuppression) dialog.showModal();
    else dialog.close();
  });

  async function supprimer() {
    try {
      await supprimerTranscript(id);
      onnaviquer({ nom: 'sources:entretiens' });
    } catch (e) {
      erreur = e instanceof Error ? e.message : 'Erreur lors de la suppression';
    }
  }

  async function generer() {
    analyseEnCours = true;
    erreur = null;
    try {
      analyse = await genererAnalyse(id);
    } catch (e) {
      erreur =
        e instanceof Error ? e.message : "Erreur lors de la génération de l'analyse";
    } finally {
      analyseEnCours = false;
    }
  }
</script>

<div class="fr-container fr-py-4w">
  <nav class="fr-breadcrumb" aria-label="vous êtes ici :">
    <ol class="fr-breadcrumb__list">
      <li>
        <a class="fr-breadcrumb__link" href="#sources/entretiens">
          Entretiens utilisateurs
        </a>
      </li>
      <li><span aria-current="page">Détail</span></li>
    </ol>
  </nav>

  {#if transcript}
    {#if erreur}
      <div class="fr-alert fr-alert--error fr-mb-3w">
        <p>{erreur}</p>
      </div>
    {/if}
    <div class="fr-mb-4w">
      <h1 class="fr-h2">Entretien #{transcript.id}</h1>
      <dl class="fr-grid-row fr-grid-row--gutters">
        <div class="fr-col-12 fr-col-md-4">
          <dt class="fr-text--bold">Date de l'entretien</dt>
          <dd>{transcript.date_entretien}</dd>
        </div>
        <div class="fr-col-12 fr-col-md-4">
          <dt class="fr-text--bold">Identité</dt>
          <dd>{identiteNom}</dd>
        </div>
        <div class="fr-col-12 fr-col-md-4">
          <dt class="fr-text--bold">Projet</dt>
          <dd>{produitNom}</dd>
        </div>
        <div class="fr-col-12">
          <dt class="fr-text--bold">Contenu</dt>
          <dd class="contenu">{transcript.contenu}</dd>
        </div>
      </dl>
    </div>

    <div class="actions">
      <button
        class="fr-btn"
        type="button"
        onclick={() => onnaviquer({ nom: 'sources:entretiens:modification', id })}
        >Modifier</button
      >
      <button
        class="fr-btn fr-btn--secondary"
        type="button"
        onclick={() => (confirmerSuppression = true)}>Supprimer</button
      >
    </div>

    <section class="fr-mt-6w">
      <h2 class="fr-h3">Analyse</h2>
      {#if !analyseChargee}
        <p>Chargement…</p>
      {:else if analyse !== null}
        <!-- eslint-disable-next-line svelte/no-at-html-tags -->
        <div class="analyse-contenu">{@html marked.parse(analyse.contenu)}</div>
      {:else if analyseEnCours}
        <p class="fr-text--sm fr-text--mention-grey">
          Analyse en cours, cela peut prendre quelques secondes…
        </p>
      {:else}
        <button class="fr-btn" type="button" onclick={generer}>
          Générer l'analyse
        </button>
      {/if}
    </section>
  {:else if erreur}
    <div class="fr-alert fr-alert--error">
      <p>{erreur}</p>
    </div>
  {:else}
    <p>Chargement…</p>
  {/if}
</div>

<dialog bind:this={dialog} class="fr-modal" aria-labelledby="modal-titre">
  <div class="fr-container fr-container--fluid fr-container-md">
    <div class="fr-grid-row fr-grid-row--center">
      <div class="fr-col-12 fr-col-md-8 fr-col-lg-6">
        <div class="fr-modal__body">
          <div class="fr-modal__header">
            <button
              class="fr-btn--close fr-btn"
              aria-controls="modal-suppression"
              onclick={() => (confirmerSuppression = false)}
            >
              Fermer
            </button>
          </div>
          <div class="fr-modal__content">
            <h1 id="modal-titre" class="fr-modal__title">
              Supprimer ce transcript ?
            </h1>
            <p>Cette action est irréversible.</p>
          </div>
          <div class="fr-modal__footer">
            <ul
              class="fr-btns-group fr-btns-group--right fr-btns-group--inline-reverse fr-btns-group--inline-lg"
            >
              <li>
                <button
                  class="fr-btn fr-btn--secondary"
                  onclick={() => (confirmerSuppression = false)}
                >
                  Annuler
                </button>
              </li>
              <li>
                <button class="fr-btn" onclick={supprimer}>Supprimer</button>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  </div>
</dialog>

<style>
  .actions {
    display: flex;
    gap: 1rem;
  }
  .contenu {
    white-space: pre-wrap;
    font-family: var(--font-family-main, Marianne, sans-serif);
    margin-top: 0.5rem;
  }
  .analyse-contenu {
    background: var(--background-alt-grey, #f6f6f6);
    padding: 1.5rem;
    border-radius: 4px;
  }
  .analyse-contenu :global(h1),
  .analyse-contenu :global(h2),
  .analyse-contenu :global(h3) {
    font-weight: bold;
    margin: 1rem 0 0.5rem;
  }
  .analyse-contenu :global(ul),
  .analyse-contenu :global(ol) {
    padding-left: 1.5rem;
    margin: 0.5rem 0;
  }
  .analyse-contenu :global(p) {
    margin: 0.5rem 0;
  }
</style>
