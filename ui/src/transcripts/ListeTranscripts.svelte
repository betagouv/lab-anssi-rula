<script lang="ts">
  import type { Vue, Transcript } from '../types';
  import { listerTranscripts } from '../api/transcripts';

  let { onnaviquer }: { onnaviquer: (v: Vue) => void } = $props();

  type Ressource = { id: number; nom: string };

  let transcripts = $state<Transcript[]>([]);
  let identiteParId = $state<Record<number, string>>({});
  let produitParId = $state<Record<number, string>>({});
  let chargement = $state(true);

  $effect(() => {
    Promise.all([
      listerTranscripts(),
      fetch('/api/identites').then((r) => r.json() as Promise<Ressource[]>),
      fetch('/api/produits').then((r) => r.json() as Promise<Ressource[]>),
    ]).then(([ts, ids, prods]) => {
      transcripts = ts;
      identiteParId = Object.fromEntries(ids.map((i) => [i.id, i.nom]));
      produitParId = Object.fromEntries(prods.map((p) => [p.id, p.nom]));
      chargement = false;
    });
  });
</script>

<div class="fr-container fr-py-4w">
  <div class="en-tete">
    <h1 class="fr-h2">Transcripts</h1>
    <dsfr-button
      label="Ajouter un transcript"
      onclick={() => onnaviquer({ nom: 'transcripts:ajout' })}
    ></dsfr-button>
  </div>

  {#if chargement}
    <p>Chargement…</p>
  {:else if transcripts.length === 0}
    <p class="fr-text--lg">Aucun transcript pour l'instant.</p>
  {:else}
    <div class="fr-table fr-table--bordered">
      <table>
        <thead>
          <tr>
            <th scope="col">Date</th>
            <th scope="col">Identité</th>
            <th scope="col">Projet</th>
            <th scope="col">Actions</th>
          </tr>
        </thead>
        <tbody>
          {#each transcripts as t (t.id)}
            <tr>
              <td>{t.date_entretien}</td>
              <td>{identiteParId[t.identite_id] ?? t.identite_id}</td>
              <td>{produitParId[t.produit_id] ?? t.produit_id}</td>
              <td class="actions">
                <dsfr-button
                  label="Voir"
                  kind="secondary"
                  onclick={() => onnaviquer({ nom: 'transcripts:detail', id: t.id })}
                ></dsfr-button>
                <dsfr-button
                  label="Modifier"
                  kind="secondary"
                  onclick={() =>
                    onnaviquer({ nom: 'transcripts:modification', id: t.id })}
                ></dsfr-button>
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  {/if}
</div>

<style>
  .en-tete {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1.5rem;
  }
  .actions {
    display: flex;
    gap: 0.5rem;
  }
</style>
