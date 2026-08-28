<script lang="ts">
  import {
    analyserTransverse,
    obtenirAnalyseTransverse,
    type AnalyseTransverse,
    type PassageTransverse,
  } from '../api/analyse_transverse';
  import type { Produit } from '../api/projets';

  let { produit }: { produit: Produit } = $props();
  let resultat = $state<AnalyseTransverse | null>(null);
  let chargement = $state(true);
  let enCours = $state(false);
  let erreur = $state('');

  $effect(() => {
    obtenirAnalyseTransverse(produit.id)
      .then((value) => (resultat = value))
      .catch((e) => {
        erreur = e instanceof Error ? e.message : 'Erreur de chargement';
      })
      .finally(() => (chargement = false));
  });

  async function analyser() {
    enCours = true;
    erreur = '';
    try {
      resultat = await analyserTransverse(produit.id);
    } catch (e) {
      erreur = e instanceof Error ? e.message : 'Erreur lors de l’analyse';
    } finally {
      enCours = false;
    }
  }

  function lien(passage: PassageTransverse) {
    if (
      passage.source === 'transcript' &&
      passage.projet_id &&
      passage.transcript_id
    )
      return `#/projets/${passage.projet_id}/entretiens/${passage.transcript_id}`;
    if (passage.source === 'idee' && passage.source_id)
      return `#/sources/featurebase/${passage.source_id}`;
    if (passage.source === 'retour_bizdev' && passage.source_id)
      return `#/sources/retours-bizdev/${passage.source_id}`;
    return null;
  }

  function libelleSource(source: PassageTransverse['source']) {
    return source === 'transcript'
      ? 'Transcript'
      : source === 'idee'
        ? 'FeatureBase'
        : 'BizDev';
  }
</script>

<section class="transverse" aria-labelledby="titre-transverse">
  <div class="titre">
    <h2 id="titre-transverse">Analyse transverse du produit</h2>
    <button class="fr-btn" disabled={enCours} onclick={analyser}
      >{enCours ? 'Analyse en cours…' : 'Analyser les données'}</button
    >
  </div>
  {#if chargement}<p>Chargement de l’analyse transverse…</p>
  {:else if erreur}<p class="erreur" role="alert">{erreur}</p>
  {:else if !resultat?.groupes.length}<p class="vide">
      Aucune analyse transverse. Lancez l’analyse pour rapprocher les données du
      produit.
    </p>
  {:else}
    {#if resultat?.calcule_le}<p class="date-calcul">
        Dernier calcul : {new Date(resultat.calcule_le).toLocaleString('fr-FR')}
      </p>{/if}
    <h3>Idées normalisées</h3>
    <div class="groupes">
      {#each resultat?.groupes ?? [] as groupe, index (groupe.nom_generique + ':' + index)}
        <details>
          <summary>{groupe.nom_generique} ({groupe.occurrences})</summary>
          <ul>
            {#each groupe.passages as passage (passage.source + ':' + passage.source_id)}
              {@const sourceLien = lien(passage)}
              <li>
                <span class="source">{libelleSource(passage.source)}</span>
                {#if sourceLien}
                  <a href={sourceLien}>{passage.verbatim}</a>
                {:else}
                  <span>{passage.verbatim}</span>
                {/if}
              </li>
            {/each}
          </ul>
        </details>
      {/each}
    </div>
  {/if}
</section>

<style>
  .titre {
    align-items: center;
    display: flex;
    gap: 1rem;
    justify-content: space-between;
  }
  h2 {
    margin-top: 0;
  }
  h3 {
    margin-top: 2rem;
  }
  .groupes {
    border-top: 1px solid var(--border-default-grey);
  }
  .groupes details {
    border-bottom: 1px solid var(--border-default-grey);
    padding: 0.75rem 0;
  }
  .groupes summary {
    cursor: pointer;
    font-weight: 700;
  }
  .groupes ul {
    display: grid;
    gap: 0.75rem;
    list-style: none;
    margin: 1rem 0 0;
    padding: 0;
  }
  .groupes li {
    display: grid;
    gap: 0.5rem;
  }
  .source {
    color: var(--text-mention-grey);
    font-size: 0.875rem;
    font-weight: 700;
  }
  .date-calcul {
    color: var(--text-mention-grey);
  }
  a {
    color: var(--text-action-high-blue-france);
  }
  .vide {
    color: var(--text-mention-grey, #666);
  }
  .erreur {
    color: #ce0500;
  }
  @media (max-width: 48rem) {
    .titre {
      align-items: stretch;
      flex-direction: column;
    }
  }
</style>
