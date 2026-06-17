<script lang="ts">
  import type { Vue, Transcript } from '../types';
  import { listerTranscripts } from '../api/transcripts';

  let { onnaviquer }: { onnaviquer: (v: Vue) => void } = $props();

  type Ressource = { id: number; nom: string };

  let transcripts = $state<Transcript[]>([]);
  let identites = $state<Ressource[]>([]);
  let produits = $state<Ressource[]>([]);
  let identiteParId = $state<Record<number, string>>({});
  let produitParId = $state<Record<number, string>>({});
  let chargement = $state(true);

  let dateDebut = $state('');
  let dateFin = $state('');
  let filtreIdentiteId = $state('');
  let filtreProjetId = $state('');

  $effect(() => {
    Promise.all([
      listerTranscripts(),
      fetch('/api/identites').then((r) => r.json() as Promise<Ressource[]>),
      fetch('/api/produits').then((r) => r.json() as Promise<Ressource[]>),
    ]).then(([ts, ids, prods]) => {
      transcripts = ts;
      identites = ids;
      produits = prods;
      identiteParId = Object.fromEntries(ids.map((i) => [i.id, i.nom]));
      produitParId = Object.fromEntries(prods.map((p) => [p.id, p.nom]));
      chargement = false;
    });
  });

  const transcriptsFiltres = $derived(
    transcripts.filter((t) => {
      if (dateDebut && t.date_entretien < dateDebut) return false;
      if (dateFin && t.date_entretien > dateFin) return false;
      if (filtreIdentiteId && t.identite_id !== Number(filtreIdentiteId))
        return false;
      if (filtreProjetId && t.produit_id !== Number(filtreProjetId)) return false;
      return true;
    })
  );
</script>

<div class="fr-container fr-py-4w">
  <div class="en-tete">
    <h1 class="fr-h2">Transcripts</h1>
    <button
      class="fr-btn"
      type="button"
      onclick={() => onnaviquer({ nom: 'transcripts:ajout' })}
    >
      Ajouter un transcript
    </button>
  </div>

  <div class="fr-grid-row fr-grid-row--gutters fr-mb-3w">
    <div class="fr-col-12 fr-col-md-3">
      <div class="fr-input-group">
        <label class="fr-label" for="date-debut">Date début</label>
        <input class="fr-input" type="date" id="date-debut" bind:value={dateDebut} />
      </div>
    </div>
    <div class="fr-col-12 fr-col-md-3">
      <div class="fr-input-group">
        <label class="fr-label" for="date-fin">Date fin</label>
        <input class="fr-input" type="date" id="date-fin" bind:value={dateFin} />
      </div>
    </div>
    <div class="fr-col-12 fr-col-md-3">
      <div class="fr-select-group">
        <label class="fr-label" for="filtre-identite">Identité</label>
        <select class="fr-select" id="filtre-identite" bind:value={filtreIdentiteId}>
          <option value="">Toutes</option>
          {#each identites as i (i.id)}
            <option value={String(i.id)}>{i.nom}</option>
          {/each}
        </select>
      </div>
    </div>
    <div class="fr-col-12 fr-col-md-3">
      <div class="fr-select-group">
        <label class="fr-label" for="filtre-projet">Projet</label>
        <select class="fr-select" id="filtre-projet" bind:value={filtreProjetId}>
          <option value="">Tous</option>
          {#each produits as p (p.id)}
            <option value={String(p.id)}>{p.nom}</option>
          {/each}
        </select>
      </div>
    </div>
  </div>

  {#if chargement}
    <p>Chargement…</p>
  {:else if transcripts.length === 0}
    <p class="fr-text--lg">Aucun transcript pour l'instant.</p>
  {:else if transcriptsFiltres.length === 0}
    <p class="fr-text--lg">
      Aucun transcript ne correspond aux filtres sélectionnés.
    </p>
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
          {#each transcriptsFiltres as t (t.id)}
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
