<script lang="ts">
  import type { Vue, Transcript } from '../types';
  import { listerTranscripts } from '../api/transcripts';
  import { hashDepuisVue } from '../navigation/routage';

  let { onnaviquer }: { onnaviquer: (v: Vue) => void } = $props();

  type Ressource = { id: number; nom: string };

  let transcripts = $state<Transcript[]>([]);
  let identites = $state<Ressource[]>([]);
  let produits = $state<Ressource[]>([]);
  let identiteParId = $state<Record<number, string>>({});
  let produitParId = $state<Record<number, string>>({});
  let chargement = $state(true);
  let erreur = $state<string | null>(null);

  let dateDebut = $state('');
  let dateFin = $state('');
  let filtreIdentiteId = $state('');
  let filtreProjetId = $state('');

  $effect(() => {
    Promise.all([
      listerTranscripts(),
      fetch('/api/identites').then((r) => r.json() as Promise<Ressource[]>),
      fetch('/api/produits').then((r) => r.json() as Promise<Ressource[]>),
    ])
      .then(([ts, ids, prods]) => {
        transcripts = ts;
        identites = ids;
        produits = prods;
        identiteParId = Object.fromEntries(ids.map((i) => [i.id, i.nom]));
        produitParId = Object.fromEntries(prods.map((p) => [p.id, p.nom]));
      })
      .catch((e) => {
        erreur = e instanceof Error ? e.message : 'Erreur lors du chargement';
      })
      .finally(() => {
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
    <div>
      <h1 class="fr-h2">Entretiens utilisateurs</h1>
      {#if !chargement}
        <p class="fr-text--sm fr-mb-0">{transcripts.length} entretien(s)</p>
      {/if}
    </div>
    <div class="actions-en-tete">
      <a class="fr-btn fr-btn--secondary" href={hashDepuisVue({ nom: 'analyses' })}
        >Historique des analyses</a
      >
      <button
        class="fr-btn"
        type="button"
        onclick={() => onnaviquer({ nom: 'sources:entretiens:ajout' })}
      >
        Ajouter un entretien
      </button>
    </div>
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

  {#if erreur}
    <div class="fr-alert fr-alert--error fr-mb-3w">
      <p>{erreur}</p>
    </div>
  {:else if chargement}
    <p>Chargement…</p>
  {:else if transcripts.length === 0}
    <p class="fr-text--lg">Aucun entretien pour l'instant.</p>
  {:else if transcriptsFiltres.length === 0}
    <p class="fr-text--lg">
      Aucun transcript ne correspond aux filtres sélectionnés.
    </p>
  {:else}
    <div class="fr-table fr-table--bordered">
      <table>
        <thead>
          <tr>
            <th scope="col">Date de l'entretien</th>
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
                <button
                  class="fr-btn fr-btn--secondary fr-btn--sm"
                  type="button"
                  onclick={() =>
                    onnaviquer({ nom: 'sources:entretiens:detail', id: t.id })}
                  >Voir</button
                >
                <button
                  class="fr-btn fr-btn--secondary fr-btn--sm"
                  type="button"
                  onclick={() =>
                    onnaviquer({ nom: 'sources:entretiens:modification', id: t.id })}
                  >Modifier</button
                >
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
  .actions-en-tete {
    display: flex;
    flex-wrap: wrap;
    gap: 0.75rem;
  }
  .actions {
    display: flex;
    gap: 0.5rem;
  }
</style>
