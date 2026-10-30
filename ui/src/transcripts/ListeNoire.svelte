<script lang="ts">
  import { onMount } from 'svelte';
  import { ErreurApi } from '../api/requete';
  import {
    ajouterTermeListeNoire,
    listerListeNoire,
    modifierTermeListeNoire,
    supprimerTermeListeNoire,
    type TermeListeNoire,
  } from './pseudonymiser_api';

  let termes = $state<TermeListeNoire[]>([]);
  let termeNouveau = $state('');
  let editionId = $state<number | null>(null);
  let editionTerme = $state('');
  let enCours = $state(false);
  let chargee = $state(false);
  let erreur = $state('');
  let message = $state('');

  async function charger() {
    try {
      termes = await listerListeNoire();
    } catch (cause) {
      erreur =
        cause instanceof Error
          ? cause.message
          : 'La liste ne peut pas être chargée.';
    } finally {
      chargee = true;
    }
  }

  async function ajouter(event: SubmitEvent) {
    event.preventDefault();
    enCours = true;
    message = '';
    erreur = '';
    try {
      await ajouterTermeListeNoire(termeNouveau);
      termeNouveau = '';
      message = 'Terme ajouté à la liste noire.';
      await charger();
    } catch (cause) {
      erreur =
        cause instanceof Error ? cause.message : 'Le terme ne peut pas être ajouté.';
    } finally {
      enCours = false;
    }
  }

  function commencerEdition(terme: TermeListeNoire) {
    editionId = terme.id;
    editionTerme = terme.terme;
    message = '';
    erreur = '';
  }

  async function enregistrerEdition(terme: TermeListeNoire) {
    enCours = true;
    erreur = '';
    message = '';
    try {
      await modifierTermeListeNoire(terme.id, editionTerme, terme.revision);
      editionId = null;
      message = 'Terme modifié.';
      await charger();
    } catch (cause) {
      erreur =
        cause instanceof ErreurApi && cause.statut === 409
          ? 'Une autre personne a modifié cette entrée. La liste a été actualisée.'
          : cause instanceof Error
            ? cause.message
            : 'Le terme ne peut pas être modifié.';
      await charger();
    } finally {
      enCours = false;
    }
  }

  async function supprimer(terme: TermeListeNoire) {
    enCours = true;
    erreur = '';
    message = '';
    try {
      await supprimerTermeListeNoire(terme.id, terme.revision);
      message = 'Terme supprimé.';
      await charger();
    } catch (cause) {
      erreur =
        cause instanceof ErreurApi && cause.statut === 409
          ? 'Une autre personne a modifié cette entrée. La liste a été actualisée.'
          : cause instanceof Error
            ? cause.message
            : 'Le terme ne peut pas être supprimé.';
      await charger();
    } finally {
      enCours = false;
    }
  }

  onMount(() => {
    void charger();
  });
</script>

<section aria-labelledby="titre-liste-noire">
  <div class="titre-page">
    <div>
      <h1 id="titre-liste-noire">Liste noire</h1>
      <p class="chapo">
        Les termes de cette liste seront masqués dans les nouvelles préparations
        seulement. Leurs masques restent obligatoires à la relecture. La liste ne
        change pas les transcripts déjà enregistrés ni leurs métadonnées.
      </p>
    </div>
    <a class="fr-btn fr-btn--secondary" href="#/">Retour à l’accueil</a>
  </div>

  <form class="ajout fr-form-group" onsubmit={ajouter}>
    <label class="fr-label" for="nouveau-terme">Ajouter un terme à masquer</label>
    <p class="fr-hint-text">
      120 caractères maximum. Les doublons sans distinction de casse sont refusés.
    </p>
    <div class="ajout-actions">
      <input
        id="nouveau-terme"
        class="fr-input"
        bind:value={termeNouveau}
        maxlength="120"
        required
        autocomplete="off"
      />
      <button class="fr-btn" type="submit" disabled={enCours}>Ajouter</button>
    </div>
  </form>

  {#if erreur}
    <p class="fr-error-text" role="alert">{erreur}</p>
  {/if}
  {#if message}
    <p class="fr-text--success" role="status">{message}</p>
  {/if}

  <ul class="termes" aria-label="Termes à masquer" aria-live="polite">
    {#if !chargee}
      <li class="vide" aria-live="polite">Chargement des termes…</li>
    {:else if termes.length}
      {#each termes as terme (terme.id)}
        <li>
          {#if editionId === terme.id}
            <label class="sr-only" for={`edition-${terme.id}`}
              >Modifier {terme.terme}</label
            >
            <input
              id={`edition-${terme.id}`}
              class="fr-input"
              bind:value={editionTerme}
              maxlength="120"
              required
              disabled={enCours}
            />
            <button
              class="fr-btn"
              type="button"
              disabled={enCours}
              onclick={() => enregistrerEdition(terme)}
            >
              Enregistrer
            </button>
            <button
              class="fr-btn fr-btn--tertiary-no-outline"
              type="button"
              disabled={enCours}
              onclick={() => (editionId = null)}
            >
              Annuler
            </button>
          {:else}
            <span class="libelle">{terme.terme}</span>
            <div class="actions-terme">
              <button
                class="fr-btn fr-btn--tertiary-no-outline"
                type="button"
                disabled={enCours}
                onclick={() => commencerEdition(terme)}
              >
                <span class="sr-only">Modifier </span>{terme.terme}
              </button>
              <button
                class="fr-btn fr-btn--tertiary-no-outline"
                type="button"
                disabled={enCours}
                aria-label={`Supprimer ${terme.terme}`}
                onclick={() => supprimer(terme)}
              >
                Supprimer
              </button>
            </div>
          {/if}
        </li>
      {/each}
    {:else}
      <li class="vide">Aucun terme à masquer. Ajoutez-en un ci-dessus.</li>
    {/if}
  </ul>
</section>

<style>
  .titre-page {
    display: flex;
    align-items: flex-end;
    justify-content: space-between;
    gap: 16px;
    margin-bottom: 32px;
  }
  h1 {
    margin: 0;
    font-size: clamp(2rem, 4vw, 2.5rem);
    line-height: 1.2;
  }
  .chapo {
    max-width: 70ch;
    margin: 8px 0 0;
    color: var(--text-mention-grey, #666);
    font-size: 18px;
  }
  .ajout {
    padding: 24px;
    border: 1px solid var(--border-default-grey, #ddd);
    background: var(--background-alt-grey, #f6f6f6);
  }
  .ajout-actions {
    display: flex;
    align-items: flex-end;
    gap: 12px;
  }
  .ajout-actions .fr-input {
    max-width: 520px;
  }
  .termes {
    display: grid;
    gap: 8px;
    margin: 24px 0 0;
    padding: 0;
    list-style: none;
  }
  .termes li {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    min-width: 0;
    padding: 12px 16px;
    border: 1px solid var(--border-default-grey, #ddd);
    background: var(--background-default-grey, #fff);
  }
  .libelle {
    overflow-wrap: anywhere;
  }
  .actions-terme {
    display: flex;
    flex-shrink: 0;
    gap: 4px;
  }
  .vide {
    color: var(--text-mention-grey, #666);
  }
  .sr-only {
    position: absolute;
    width: 1px;
    height: 1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    white-space: nowrap;
  }
  @media (max-width: 600px) {
    .titre-page,
    .ajout-actions,
    .termes li {
      align-items: stretch;
      flex-direction: column;
    }
    .ajout-actions .fr-input {
      max-width: none;
    }
    .actions-terme {
      flex-wrap: wrap;
    }
  }
</style>
