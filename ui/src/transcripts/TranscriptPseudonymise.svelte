<script lang="ts">
  import {
    CATEGORIES_PSEUDONYMISATION,
    decouperTranscriptPseudonymise,
  } from './marqueurs-pseudonymisation';

  let {
    contenu = $bindable(),
    mode = 'lecture',
    id = 'transcript',
    titre = 'Transcript pseudonymisé',
    lignes = 14,
    legende = true,
  }: {
    contenu: string;
    mode?: 'lecture' | 'edition';
    id?: string;
    titre?: string;
    lignes?: number;
    legende?: boolean;
  } = $props();
  let segments = $derived(decouperTranscriptPseudonymise(contenu));
  let pseudonymise = $derived(
    segments.some((segment) => segment.categorie !== null)
  );
  let idTitre = $derived(
    mode === 'lecture' ? 'titre-transcript-pseudonymise' : `${id}-titre`
  );
  let defilementX = $state(0);
  let defilementY = $state(0);
</script>

<section aria-labelledby={mode === 'lecture' ? idTitre : undefined}>
  {#if mode === 'edition'}
    <label class="fr-label" for={id}>{titre}</label>
  {:else}
    <h3 id={idTitre}>{titre}</h3>
  {/if}
  {#if pseudonymise && legende}
    <p class="aide-copie">
      {#if mode === 'edition'}
        Les pseudonymes colorés restent modifiables. Le texte sélectionné et copié
        conserve les marqueurs.
      {:else}
        Les valeurs d’origine ont été remplacées par ces pseudonymes. Sélectionnez le
        texte pour le copier.
      {/if}
    </p>
    <ul class="legende" aria-label="Légende des catégories pseudonymisées">
      {#each CATEGORIES_PSEUDONYMISATION as categorie (categorie.id)}
        <li>
          <span class={`pastille pastille--${categorie.id}`} aria-hidden="true"
          ></span>
          {categorie.libelle}
        </li>
      {/each}
    </ul>
  {/if}
  {#if mode === 'edition'}
    <div class="editeur">
      <pre
        class="transcript superposition"
        aria-hidden="true"
        style={`transform: translate(${-defilementX}px, ${-defilementY}px)`}>{#each segments as segment, index (index)}{#if segment.categorie}<span
              class={`pseudonyme pseudonyme--${segment.categorie.id}`}
              title={segment.categorie.libelle}>{segment.texte}</span
            >{:else}{segment.texte}{/if}{/each}</pre>
      <textarea
        class="fr-input transcript saisie"
        {id}
        bind:value={contenu}
        rows={lignes}
        spellcheck="false"
        onscroll={(event) => {
          defilementX = event.currentTarget.scrollLeft;
          defilementY = event.currentTarget.scrollTop;
        }}
      ></textarea>
    </div>
  {:else}
    <pre
      class="transcript">{#each segments as segment, index (index)}{#if segment.categorie}<span
            class={`pseudonyme pseudonyme--${segment.categorie.id}`}
            aria-label={`${segment.categorie.libelle} : ${segment.texte}`}
            title={segment.categorie.libelle}>{segment.texte}</span
          >{:else}{segment.texte}{/if}{/each}</pre>
  {/if}
</section>

<style>
  .aide-copie {
    color: var(--text-default-grey);
    margin-bottom: 1rem;
  }
  h3 {
    margin: 3rem 0 1.5rem;
  }
  .legende {
    display: flex;
    flex-wrap: wrap;
    gap: 0.75rem 1.25rem;
    list-style: none;
    margin: 0 0 1rem;
    padding: 0;
  }
  .legende li {
    align-items: center;
    display: inline-flex;
    gap: 0.375rem;
  }
  .pastille {
    border-radius: 0.125rem;
    height: 0.75rem;
    width: 0.75rem;
  }
  .editeur {
    position: relative;
  }
  .transcript {
    background: var(--background-alt-grey);
    border-left: 0.25rem solid var(--border-default-grey);
    max-height: 60vh;
    overflow-y: auto;
    overflow-wrap: anywhere;
    padding: 1.5rem;
    user-select: text;
    white-space: pre-wrap;
  }
  .superposition,
  .saisie {
    box-sizing: border-box;
    font: inherit;
    line-height: 1.5;
    margin: 0;
    overflow-wrap: anywhere;
    padding: 1.5rem;
    tab-size: 2;
    width: 100%;
  }
  .superposition {
    border: 1px solid transparent;
    inset: 0;
    max-height: none;
    overflow: hidden;
    pointer-events: none;
    position: absolute;
    user-select: none;
    white-space: pre-wrap;
  }
  .saisie {
    background: transparent;
    border: 1px solid var(--border-plain-grey);
    color: transparent;
    min-height: 0;
    position: relative;
    resize: vertical;
    -webkit-text-fill-color: transparent;
    caret-color: var(--text-default-grey);
  }
  .saisie::selection {
    background: rgb(0 0 145 / 25%);
  }
  .pseudonyme {
    border-radius: 0.2rem;
    box-decoration-break: clone;
    font-weight: 700;
    padding: 0 0.125rem;
  }
  .pseudonyme--identite,
  .pastille--identite {
    background: var(--background-contrast-green-emeraude, #e4f5e8);
    color: var(--text-action-high-green-emeraude, #125a2e);
  }
  .pseudonyme--coordonnees,
  .pastille--coordonnees {
    background: var(--background-contrast-purple-glycine, #f0e7ff);
    color: var(--text-action-high-purple-glycine, #5b2c91);
  }
  .pseudonyme--organisation,
  .pastille--organisation {
    background: var(--background-contrast-yellow-moutarde, #fff2cc);
    color: var(--text-action-high-yellow-moutarde, #6a4b00);
  }
  .pseudonyme--secret,
  .pastille--secret {
    background: var(--background-contrast-red-marianne, #fde8e7);
    color: var(--text-action-high-red-marianne, #8f1d1d);
  }
  .pseudonyme--donnee-sensible,
  .pastille--donnee-sensible {
    background: var(--background-contrast-green-menthe, #e0f2f1);
    color: var(--text-action-high-green-menthe, #005d58);
  }
  .pseudonyme--technologie-ou-produit,
  .pastille--technologie-ou-produit {
    background: var(--background-contrast-blue-cumulus, #e8f1fc);
    color: var(--text-action-high-blue-cumulus, #004b9b);
  }
</style>
