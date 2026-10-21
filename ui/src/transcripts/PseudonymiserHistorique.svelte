<script lang="ts">
  import { onMount } from 'svelte';
  import SuppressionConfirmee from '../composants/SuppressionConfirmee.svelte';
  import {
    listerTranscriptsPdf,
    nomPseudonymise,
    supprimerTranscriptPdf,
    type TranscriptPdf,
  } from './pseudonymiser_api';

  let {
    produitId,
    onconsulter,
  }: { produitId: number; onconsulter: (id: number) => void } = $props();
  let transcripts = $state<TranscriptPdf[]>([]);
  let recherche = $state('');
  let chargement = $state(true);
  let erreur = $state('');
  const filtres = $derived(
    transcripts.filter((item) =>
      `${item.nom_source} ${item.date_entretien ?? ''}`
        .toLocaleLowerCase('fr')
        .includes(recherche.toLocaleLowerCase('fr'))
    )
  );

  async function charger() {
    try {
      transcripts = await listerTranscriptsPdf(produitId);
    } catch (cause) {
      erreur = cause instanceof Error ? cause.message : 'Historique indisponible.';
    } finally {
      chargement = false;
    }
  }

  onMount(() => void charger());
</script>

<div class="historique">
  <div class="entete-historique">
    <div>
      <h2>Transcripts importés</h2>
      {#if !chargement}<p>
          {transcripts.length} transcript(s) · du plus récent au plus ancien
        </p>{/if}
    </div>
    <div class="fr-input-group recherche">
      <label class="fr-label" for="recherche-transcripts"
        >Rechercher un transcript</label
      >
      <input
        class="fr-input"
        id="recherche-transcripts"
        type="search"
        bind:value={recherche}
      />
    </div>
  </div>
  {#if erreur}<p class="fr-alert fr-alert--error" role="alert">{erreur}</p>
  {:else if chargement}<p role="status" aria-live="polite">
      Chargement de l’historique…
    </p>
  {:else if !filtres.length}<div class="vide">
      <p>
        {transcripts.length
          ? 'Aucun transcript ne correspond à la recherche.'
          : 'Aucun transcript confirmé pour ce produit.'}
      </p>
    </div>
  {:else}
    <div class="tableau">
      <table>
        <thead
          ><tr
            ><th scope="col">Transcript</th><th scope="col">Type</th><th scope="col"
              >Importé le</th
            ><th scope="col">Entretien du</th><th scope="col">Actions</th></tr
          ></thead
        >
        <tbody>
          {#each filtres as item (item.id)}
            <tr>
              <td class="nom">{nomPseudonymise(item.nom_source)}</td>
              <td>{item.type_source === 'bizdev' ? 'BizDev' : 'Produit'}</td>
              <td
                >{new Intl.DateTimeFormat('fr-FR', { dateStyle: 'short' }).format(
                  new Date(item.cree_le)
                )}</td
              >
              <td>{item.date_entretien ?? '—'}</td>
              <td class="actions">
                <button
                  class="fr-btn fr-btn--secondary fr-btn--sm"
                  type="button"
                  onclick={() => onconsulter(item.id)}>Consulter</button
                >
                <a
                  class="fr-btn fr-btn--tertiary-no-outline fr-icon-download-line fr-btn--icon-left"
                  href={`/api/transcripts-pdf/${item.id}/pdf`}
                  aria-label={`Télécharger ${nomPseudonymise(item.nom_source)} en PDF`}
                  download={nomPseudonymise(item.nom_source)}>Télécharger</a
                >
                <SuppressionConfirmee
                  modalId={`suppression-pseudonymiser-${item.id}`}
                  titre={`Supprimer le transcript « ${nomPseudonymise(item.nom_source)} » ?`}
                  description="Le transcript pseudonymisé sera supprimé définitivement. Cette action est irréversible."
                  onconfirmer={() => supprimerTranscriptPdf(item.id)}
                  onsucces={() =>
                    (transcripts = transcripts.filter(
                      (source) => source.id !== item.id
                    ))}
                />
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
    <ul class="cartes">
      {#each filtres as item (item.id)}
        <li class="carte">
          <strong>{nomPseudonymise(item.nom_source)}</strong>
          <span
            >{item.type_source === 'bizdev'
              ? 'Retour BizDev'
              : 'Entretien utilisateur'} · entretien du {item.date_entretien ??
              'date non renseignée'}</span
          >
          <span
            >Importé le {new Intl.DateTimeFormat('fr-FR', {
              dateStyle: 'short',
            }).format(new Date(item.cree_le))}</span
          >
          <div class="actions">
            <button
              class="fr-btn fr-btn--secondary fr-btn--sm"
              type="button"
              onclick={() => onconsulter(item.id)}>Consulter</button
            >
            <a
              class="fr-btn fr-btn--tertiary-no-outline fr-icon-download-line fr-btn--icon-left"
              href={`/api/transcripts-pdf/${item.id}/pdf`}
              download={nomPseudonymise(item.nom_source)}>Télécharger PDF</a
            >
            <SuppressionConfirmee
              modalId={`suppression-pseudonymiser-mobile-${item.id}`}
              titre={`Supprimer le transcript « ${nomPseudonymise(item.nom_source)} » ?`}
              description="Le transcript pseudonymisé sera supprimé définitivement. Cette action est irréversible."
              onconfirmer={() => supprimerTranscriptPdf(item.id)}
              onsucces={() =>
                (transcripts = transcripts.filter(
                  (source) => source.id !== item.id
                ))}
            />
          </div>
        </li>
      {/each}
    </ul>
  {/if}
</div>

<style>
  .historique {
    display: grid;
    gap: 24px;
  }
  .entete-historique {
    display: flex;
    flex-wrap: wrap;
    align-items: flex-end;
    justify-content: space-between;
    gap: 16px;
  }
  h2 {
    margin: 0;
    font-size: 24px;
  }
  .entete-historique p {
    margin: 4px 0 0;
    color: var(--text-mention-grey, #666);
    font-size: 14px;
  }
  .recherche {
    flex: 0 1 320px;
    margin: 0;
  }
  .tableau {
    overflow-x: auto;
    border: 1px solid var(--border-default-grey);
  }
  table {
    width: 100%;
    min-width: 720px;
    border-collapse: collapse;
    font-size: 14px;
  }
  th {
    padding: 12px 16px;
    background: var(--background-alt-grey);
    border-bottom: 2px solid var(--border-default-grey);
    text-align: left;
    white-space: nowrap;
  }
  td {
    padding: 14px 16px;
    border-bottom: 1px solid var(--border-default-grey);
    vertical-align: middle;
  }
  td.nom {
    overflow-wrap: anywhere;
    font-weight: 600;
  }
  .actions {
    display: flex;
    align-items: center;
    gap: 8px;
    white-space: nowrap;
  }
  .actions :global(.fr-btn) {
    margin: 0;
  }
  .vide {
    padding: 40px 24px;
    border: 1px dashed var(--border-default-grey);
    text-align: center;
  }
  .cartes {
    display: none;
    margin: 0;
    padding: 0;
    list-style: none;
  }
  .carte {
    display: grid;
    gap: 12px;
    border: 1px solid var(--border-default-grey);
    padding: 16px;
  }
  .carte > strong {
    overflow-wrap: anywhere;
  }
  .carte .actions {
    flex-wrap: wrap;
    white-space: normal;
  }
  @media (max-width: 48rem) {
    .tableau {
      display: none;
    }
    .cartes {
      display: grid;
      gap: 12px;
    }
    .actions {
      align-items: flex-start;
      flex-direction: column;
    }
    .carte .actions {
      align-items: center;
      flex-direction: row;
    }
  }
</style>
