<script lang="ts">
  import {
    analyserTransverse,
    obtenirAnalyseTransverse,
    type AnalyseTransverse,
  } from '../api/analyse_transverse';
  import type { Produit } from '../api/projets';
  import type { Membre } from '../types';
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

  function lien(membre: Membre) {
    return membre.source === 'transcript' && membre.transcript_id
      ? `#/transcripts/${membre.transcript_id}`
      : membre.source === 'idee'
        ? '#/fonctionnalites'
        : '#/retours-bizdev';
  }

  function lienBesoin(besoin: AnalyseTransverse['besoins'][number]) {
    return besoin.source === 'transcript' && besoin.transcript_id
      ? `#/transcripts/${besoin.transcript_id}`
      : besoin.source === 'idee'
        ? '#/fonctionnalites'
        : '#/retours-bizdev';
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
  {:else if !resultat?.besoins.length && !resultat?.correspondances.length}<p
      class="vide"
    >
      Aucune analyse transverse. Lancez l’analyse pour rapprocher les données du
      produit.
    </p>
  {:else}
    {#if resultat?.calcule_le}<p class="date-calcul">
        Dernier calcul : {new Date(resultat.calcule_le).toLocaleString('fr-FR')}
      </p>{/if}
    <h3>Besoins normalisés</h3>
    {#if resultat?.besoins.length}<ul class="besoins">
        {#each resultat.besoins as besoin (besoin.id)}<li>
            <a href={lienBesoin(besoin)}><strong>{besoin.nom_generique}</strong></a
            ><span>{besoin.source}</span>
          </li>{/each}
      </ul>{:else}<p class="vide">Aucun besoin détecté.</p>{/if}
    <h3>Correspondances</h3>
    {#if resultat?.correspondances.length}<div class="clusters">
        {#each resultat.correspondances as cluster (cluster.libelle)}<details>
            <summary>{cluster.libelle} ({cluster.occurrences})</summary>
            <ul>
              {#each cluster.membres as membre (membre.source + membre.source_id)}<li
                >
                  <a href={lien(membre)}>{membre.texte}</a>
                </li>{/each}
            </ul>
          </details>{/each}
      </div>{:else}<p class="vide">Aucune correspondance détectée.</p>{/if}
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
  .besoins,
  .clusters {
    border-top: 1px solid var(--border-default-grey);
  }
  .besoins {
    list-style: none;
    margin: 0;
    padding: 0;
  }
  .besoins li {
    align-items: center;
    border-bottom: 1px solid var(--border-default-grey);
    display: flex;
    gap: 1rem;
    justify-content: space-between;
    padding: 0.75rem 0;
  }
  .besoins span {
    color: var(--text-mention-grey);
  }
  .date-calcul {
    color: var(--text-mention-grey);
  }
  .clusters details {
    border-bottom: 1px solid var(--border-default-grey);
    padding: 0.75rem 0;
  }
  .clusters summary {
    cursor: pointer;
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
