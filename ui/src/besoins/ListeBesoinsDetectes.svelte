<script lang="ts">
  import type { BesoinDetecte } from '../api/besoins';
  import { analyserBesoins, listerBesoins } from '../api/besoins';
  import { hashDepuisVue } from '../navigation/routage';
  import type { SourceBesoin } from '../types';

  const sources: Array<{ id: SourceBesoin; label: string; description: string }> = [
    {
      id: 'transcript',
      label: 'Entretiens utilisateurs',
      description:
        'Extraction des besoins et fonctionnalités exprimés dans les entretiens.',
    },
    {
      id: 'retour_bizdev',
      label: 'Retours BizDev',
      description:
        'Regroupement des demandes commerciales en noms de fonctionnalités génériques.',
    },
    {
      id: 'idee',
      label: 'Demandes FeatureBase',
      description:
        'Normalisation des demandes FeatureBase avant leur rapprochement.',
    },
  ];

  let source = $state<SourceBesoin>('transcript');
  let besoins = $state<BesoinDetecte[]>([]);
  let chargement = $state(true);
  let analyseEnCours = $state(false);
  let erreur = $state<string | null>(null);

  function charger(sourceACharger: SourceBesoin) {
    chargement = true;
    erreur = null;
    listerBesoins(sourceACharger)
      .then((resultats) => {
        if (source === sourceACharger) besoins = resultats;
      })
      .catch((e) => {
        if (source === sourceACharger) {
          erreur = e instanceof Error ? e.message : 'Erreur lors du chargement';
        }
      })
      .finally(() => {
        if (source === sourceACharger) chargement = false;
      });
  }

  function changerSource(nouvelleSource: SourceBesoin) {
    source = nouvelleSource;
  }

  async function analyserSource() {
    analyseEnCours = true;
    erreur = null;
    try {
      besoins = await analyserBesoins(source);
    } catch (e) {
      erreur = e instanceof Error ? e.message : 'Erreur lors de l’analyse';
    } finally {
      analyseEnCours = false;
    }
  }

  $effect(() => charger(source));

  const sourceCourante = $derived(sources.find((item) => item.id === source));
</script>

<div class="fr-container fr-py-4w">
  <div class="en-tete">
    <div>
      <p class="fr-breadcrumb fr-mb-1w">Analyse des besoins</p>
      <h1 class="fr-h2 fr-mb-1w">Analyse des besoins</h1>
      <p class="fr-text--sm fr-mb-0">
        Chaque source est analysée selon son propre traitement. Les résultats
        convergent vers un nom générique utilisé ensuite par les correspondances.
      </p>
    </div>
    {#if !chargement}
      <span class="fr-badge fr-badge--info">{besoins.length} besoin(s)</span>
    {/if}
  </div>

  <div class="vues-sources" role="tablist" aria-label="Source à analyser">
    {#each sources as item (item.id)}
      <button
        class:active={source === item.id}
        class="fr-btn fr-btn--tertiary-no-outline"
        type="button"
        role="tab"
        aria-selected={source === item.id}
        onclick={() => changerSource(item.id)}
      >
        {item.label}
      </button>
    {/each}
  </div>

  <div class="fr-callout fr-mb-3w">
    <h2 class="fr-callout__title">{sourceCourante?.label}</h2>
    <p class="fr-mb-0">{sourceCourante?.description}</p>
  </div>

  <div class="actions fr-mb-3w">
    <button
      class="fr-btn"
      type="button"
      onclick={analyserSource}
      disabled={analyseEnCours || chargement}
    >
      {analyseEnCours ? 'Analyse en cours…' : 'Analyser cette source'}
    </button>
    <span class="fr-hint-text">
      L’analyse peut produire des résultats différents selon la source.
    </span>
  </div>

  {#if erreur}
    <div class="fr-alert fr-alert--error fr-mb-3w" role="alert">
      <p>{erreur}</p>
    </div>
  {:else if chargement}
    <p>Chargement…</p>
  {:else if besoins.length === 0}
    <div class="fr-alert fr-alert--info">
      <p>
        Aucun besoin analysé pour cette source. Lancez l’analyse pour créer les noms
        génériques.
      </p>
    </div>
  {:else}
    <div class="fr-table fr-table--bordered tableau-besoins">
      <table>
        <caption class="sr-only"
          >Résultats de l’analyse pour {sourceCourante?.label}</caption
        >
        <thead>
          <tr>
            <th scope="col">Nom générique</th>
            <th scope="col">Donnée source</th>
            <th scope="col">Verbatim</th>
            <th scope="col">Origine</th>
          </tr>
        </thead>
        <tbody>
          {#each besoins as besoin (besoin.id)}
            <tr>
              <td class="nom-generique">{besoin.nom_generique}</td>
              <td class="texte-source">{besoin.texte_original}</td>
              <td class="verbatim">{besoin.verbatim ?? '—'}</td>
              <td>
                {#if besoin.transcript_id !== null}
                  <a
                    href={hashDepuisVue({
                      nom: 'sources:entretiens:detail',
                      id: besoin.transcript_id,
                    })}>Entretien #{besoin.transcript_id}</a
                  >
                {:else}
                  {source === 'idee'
                    ? `Demande #${besoin.source_id}`
                    : `Retour #${besoin.source_id}`}
                {/if}
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
    align-items: flex-start;
    display: flex;
    gap: 1rem;
    justify-content: space-between;
    margin-bottom: 1.5rem;
  }

  .fr-breadcrumb {
    color: var(--text-mention-grey, #666);
    font-size: 0.875rem;
  }

  .vues-sources {
    border-bottom: 1px solid var(--border-default-grey, #ddd);
    display: flex;
    flex-wrap: wrap;
    gap: 0.25rem;
    margin-bottom: 1.5rem;
  }

  .vues-sources button {
    border-bottom: 3px solid transparent;
    border-radius: 0;
  }

  .vues-sources button.active {
    border-bottom-color: var(--border-action-high-blue-france, #000091);
    font-weight: 700;
  }

  .actions {
    align-items: center;
    display: flex;
    flex-wrap: wrap;
    gap: 1rem;
  }

  .tableau-besoins {
    overflow-x: auto;
  }

  .nom-generique {
    font-weight: 700;
    min-width: 14rem;
  }

  .texte-source,
  .verbatim {
    max-width: 28rem;
    min-width: 16rem;
    white-space: pre-wrap;
  }

  .verbatim {
    color: var(--text-mention-grey, #666);
    font-style: italic;
  }

  .sr-only {
    border: 0;
    clip: rect(0, 0, 0, 0);
    height: 1px;
    margin: -1px;
    overflow: hidden;
    padding: 0;
    position: absolute;
    width: 1px;
  }

  @media (max-width: 767px) {
    .en-tete {
      display: block;
    }

    .en-tete .fr-badge {
      display: inline-block;
      margin-top: 1rem;
    }
  }
</style>
