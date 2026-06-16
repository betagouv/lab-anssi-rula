<script lang="ts">
  import type { Vue, Transcript } from '../types';
  import { obtenirTranscript, supprimerTranscript } from '../api/transcripts';

  let { id, onnaviquer }: { id: number; onnaviquer: (v: Vue) => void } = $props();

  type Ressource = { id: number; nom: string };

  let transcript = $state<Transcript | null>(null);
  let identiteNom = $state('');
  let produitNom = $state('');
  let confirmerSuppression = $state(false);
  let dialog = $state<HTMLDialogElement | null>(null);

  $effect(() => {
    Promise.all([
      obtenirTranscript(id),
      fetch('/api/identites').then((r) => r.json() as Promise<Ressource[]>),
      fetch('/api/produits').then((r) => r.json() as Promise<Ressource[]>),
    ]).then(([t, ids, prods]) => {
      transcript = t;
      identiteNom =
        ids.find((i) => i.id === t.identite_id)?.nom ?? String(t.identite_id);
      produitNom =
        prods.find((p) => p.id === t.produit_id)?.nom ?? String(t.produit_id);
    });
  });

  $effect(() => {
    if (!dialog) return;
    if (confirmerSuppression) dialog.showModal();
    else dialog.close();
  });

  async function supprimer() {
    await supprimerTranscript(id);
    onnaviquer({ nom: 'transcripts:liste' });
  }
</script>

<div class="fr-container fr-py-4w">
  <nav class="fr-breadcrumb" aria-label="vous êtes ici :">
    <ol class="fr-breadcrumb__list">
      <li>
        <a
          href="#transcripts"
          class="fr-breadcrumb__link"
          onclick={(e) => {
            e.preventDefault();
            onnaviquer({ nom: 'transcripts:liste' });
          }}
        >
          Transcripts
        </a>
      </li>
      <li><span aria-current="page">Détail</span></li>
    </ol>
  </nav>

  {#if transcript}
    <div class="fr-mb-4w">
      <h1 class="fr-h2">Transcript #{transcript.id}</h1>
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
      <dsfr-button
        label="Modifier"
        onclick={() => onnaviquer({ nom: 'transcripts:modification', id })}
      ></dsfr-button>
      <dsfr-button
        label="Supprimer"
        kind="secondary"
        onclick={() => (confirmerSuppression = true)}
      ></dsfr-button>
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
</style>
