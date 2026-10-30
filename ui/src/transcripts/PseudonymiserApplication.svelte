<script lang="ts">
  import { onMount } from 'svelte';
  import { listerProduits, type Produit } from './pseudonymiser_api';
  import ImportTranscriptPdf from './ImportTranscriptPdf.svelte';
  import PseudonymiserHistorique from './PseudonymiserHistorique.svelte';
  import PseudonymiserDetail from './PseudonymiserDetail.svelte';
  import ListeTermes from './ListeTermes.svelte';

  let produits = $state<Produit[]>([]);
  let erreur = $state('');
  let onglet = $state<'import' | 'historique' | 'detail'>('import');
  let typeSource = $state<'produit' | 'bizdev'>('produit');
  let theme = $state<'light' | 'dark'>('dark');
  let transcriptId = $state<number | null>(null);
  let hash = $state(window.location.hash);
  const estListeBlanche = $derived(hash === '#/liste-blanche');
  const estListeNoire = $derived(hash === '#/liste-noire');
  const produitId = $derived(Number(hash.match(/^#\/produits\/(\d+)/)?.[1]));
  const produit = $derived(produits.find((item) => item.id === produitId));

  async function charger() {
    try {
      produits = await listerProduits();
    } catch (cause) {
      erreur = cause instanceof Error ? cause.message : 'Erreur de chargement';
    }
  }

  function actualiserRoute() {
    hash = window.location.hash;
    onglet = 'import';
    transcriptId = null;
  }

  function choisirProduit(id: number) {
    window.location.hash = `#/produits/${id}`;
  }

  function afficherTheme(valeur: 'light' | 'dark') {
    theme = valeur;
    localStorage.setItem('rula-theme', valeur);
    document.documentElement.dataset.frTheme = valeur;
  }

  onMount(() => {
    theme = localStorage.getItem('rula-theme') === 'light' ? 'light' : 'dark';
    document.documentElement.dataset.frTheme = theme;
    void charger();
    window.addEventListener('hashchange', actualiserRoute);
    return () => window.removeEventListener('hashchange', actualiserRoute);
  });
</script>

<div class="application" class:theme-clair={theme === 'light'}>
  <header class="entete">
    <div class="entete-interieur">
      <a class="marque" href="#/" aria-label="RULA, choisir un produit">
        <span class="fr-logo">République<br />Française</span>
        <img src="/anssi.svg" alt="ANSSI" />
        <span class="service">
          <span class="service-titre">RULA</span>
          <span>Import et pseudonymisation de transcripts PDF</span>
        </span>
      </a>
      <nav class="actions" aria-label="Navigation principale">
        {#if produit}
          <a class="changer" href="#/">Changer de produit</a>
        {/if}
        <a
          class="liste-blanche"
          href="#/liste-blanche"
          aria-current={estListeBlanche ? 'page' : undefined}
        >
          Liste blanche
        </a>
        <a
          class="liste-blanche"
          href="#/liste-noire"
          aria-current={estListeNoire ? 'page' : undefined}
        >
          Liste noire
        </a>
        <button
          class="fr-btn fr-btn--tertiary-no-outline theme"
          type="button"
          aria-label={theme === 'dark'
            ? 'Activer le thème clair'
            : 'Activer le thème sombre'}
          onclick={() => afficherTheme(theme === 'dark' ? 'light' : 'dark')}
          >{theme === 'dark' ? '☀ Thème clair' : '☾ Thème sombre'}</button
        >
      </nav>
    </div>
  </header>

  {#if estListeBlanche || estListeNoire}
    <main class="page">
      {#key estListeNoire ? 'noire' : 'blanche'}
        <ListeTermes couleur={estListeNoire ? 'noire' : 'blanche'} />
      {/key}
    </main>
  {:else if erreur}
    <main class="message" role="alert">{erreur}</main>
  {:else if !produits.length}
    <main class="message" aria-live="polite">Chargement des produits…</main>
  {:else if !produit}
    <main class="page choix-produit">
      <h1>Choisissez un produit</h1>
      <p class="chapo">Les transcripts importés sont rattachés au produit choisi.</p>
      <div class="cartes-produits">
        {#each produits as item (item.id)}
          <button
            class="carte-produit"
            type="button"
            onclick={() => choisirProduit(item.id)}
          >
            <span
              class="badge"
              class:mss={item.nom === 'MSS'}
              class:msc={item.nom === 'MSC'}
            >
              {item.nom}
            </span>
            <strong>{item.nom}</strong>
            <span class="action"
              >Importer un transcript <span aria-hidden="true">→</span></span
            >
          </button>
        {/each}
      </div>
    </main>
  {:else if onglet === 'detail' && transcriptId !== null}
    <PseudonymiserDetail
      {transcriptId}
      produitNom={produit.nom}
      retour={() => {
        transcriptId = null;
        onglet = 'historique';
      }}
    />
  {:else}
    <main class="page">
      <div class="titre-page">
        <div>
          <h1>
            Transcripts PDF <span
              class="badge"
              class:mss={produit.nom === 'MSS'}
              class:msc={produit.nom === 'MSC'}>{produit.nom}</span
            >
          </h1>
          <p class="chapo">
            Importez un compte rendu pour le pseudonymiser et relisez les éléments
            détectés avant de le conserver.
          </p>
        </div>
      </div>
      <div class="onglets" role="tablist" aria-label="Parcours des transcripts">
        <button
          role="tab"
          aria-selected={onglet === 'import'}
          class:actif={onglet === 'import'}
          onclick={() => (onglet = 'import')}>Importer un transcript</button
        >
        <button
          role="tab"
          aria-selected={onglet === 'historique'}
          class:actif={onglet === 'historique'}
          onclick={() => (onglet = 'historique')}>Transcripts importés</button
        >
      </div>
      {#if onglet === 'import'}
        <section class="panneau" aria-label="Importer un transcript PDF">
          <fieldset class="choix-source">
            <legend>Type de compte rendu</legend>
            <label
              ><input
                type="radio"
                name="type-source"
                value="produit"
                bind:group={typeSource}
              /> Entretien utilisateur</label
            >
            <label
              ><input
                type="radio"
                name="type-source"
                value="bizdev"
                bind:group={typeSource}
              /> Retour BizDev</label
            >
          </fieldset>
          {#key `${produit.id}-${typeSource}`}
            <ImportTranscriptPdf
              produitId={produit.id}
              {typeSource}
              onconfirme={() => (onglet = 'historique')}
            />
          {/key}
        </section>
      {:else}
        <section class="panneau">
          <PseudonymiserHistorique
            produitId={produit.id}
            onconsulter={(id) => {
              transcriptId = id;
              onglet = 'detail';
            }}
          />
        </section>
      {/if}
    </main>
  {/if}
</div>

<style>
  :global(*) {
    box-sizing: border-box;
  }
  :global(body) {
    margin: 0;
    font-family: Marianne, Arial, sans-serif;
  }
  :global(html[data-fr-theme='dark']) {
    color-scheme: dark;
    background: #161616;
  }
  :global(html[data-fr-theme='light']) {
    color-scheme: light;
    background: #fff;
  }
  .application {
    min-height: 100vh;
    color: var(--text-default-grey, #161616);
    background: var(--background-default-grey, #fff);
  }
  :global(html[data-fr-theme='dark']) .application {
    --text-default-grey: #f6f6f6;
    --text-title-grey: #f6f6f6;
    --text-default-info: #8bb7ff;
    --border-default-grey: #353535;
    --border-action-high-blue-france: #8585f6;
    --text-action-high-blue-france: #8585f6;
    --background-default-grey: #161616;
    --background-alt-grey: #1e1e1e;
    --background-contrast-grey: #2a2a2a;
    --background-contrast-info: #21213f;
    --text-default-success: #3bea7e;
    --background-contrast-success: #19281f;
    --border-active-blue-france: #8585f6;
  }
  :global(html[data-fr-theme='light']) .application {
    --text-default-grey: #161616;
    --text-title-grey: #161616;
    --text-action-high-blue-france: #000091;
    --border-default-grey: #ddd;
    --background-default-grey: #fff;
    --background-alt-grey: #f6f6f6;
    --background-contrast-grey: #eee;
    --background-contrast-info: #e3e3fd;
    --border-action-high-blue-france: #000091;
    --border-active-blue-france: #000091;
  }
  .entete {
    background: var(--background-default-grey);
    box-shadow: 0 1px 3px rgb(0 0 18 / 16%);
  }
  .entete-interieur {
    max-width: 1232px;
    min-height: 88px;
    margin: 0 auto;
    padding: 14px 16px;
    display: flex;
    align-items: center;
    gap: 16px 24px;
    flex-wrap: wrap;
  }
  .marque {
    display: flex;
    align-items: center;
    gap: 16px;
    color: inherit;
    text-decoration: none;
  }
  .marque img {
    width: 52px;
    height: 52px;
  }
  .service {
    display: grid;
    gap: 2px;
    color: var(--text-default-grey);
    font-size: 14px;
  }
  .service-titre {
    font-size: 20px;
    font-weight: 700;
  }
  .actions {
    margin-left: auto;
    display: flex;
    align-items: center;
    gap: 16px;
    flex-wrap: wrap;
  }
  .theme {
    margin: 0;
  }
  .page {
    max-width: 1032px;
    margin: 0 auto;
    padding: 40px 16px 80px;
  }
  .choix-produit {
    padding-top: 40px;
  }
  h1 {
    margin: 0;
    font-size: clamp(2rem, 4vw, 2.5rem);
    line-height: 1.2;
  }
  .chapo {
    margin: 8px 0 32px;
    color: var(--text-mention-grey, #666);
    font-size: 18px;
  }
  .cartes-produits {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 24px;
  }
  .carte-produit {
    min-height: 210px;
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
    padding: 32px;
    border: 1px solid var(--border-default-grey);
    border-bottom: 4px solid var(--border-action-high-blue-france, #8585f6);
    background: var(--background-default-grey);
    color: inherit;
    text-align: left;
    cursor: pointer;
  }
  .carte-produit:hover {
    background: var(--background-alt-grey);
  }
  .carte-produit strong {
    font-size: 24px;
  }
  .badge {
    display: inline-block;
    padding: 1px 6px;
    border-radius: 4px;
    font-size: 12px;
    font-weight: 700;
  }
  .badge.mss {
    background: #19281f;
    color: #3bea7e;
  }
  .badge.msc {
    background: #21213f;
    color: #8585f6;
  }
  .action {
    margin-top: auto;
    color: var(--text-action-high-blue-france, #8585f6);
  }
  .titre-page {
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    gap: 16px;
  }
  .titre-page h1 {
    display: flex;
    align-items: center;
    gap: 12px;
  }
  .onglets {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    padding: 0 4px;
  }
  .onglets button {
    min-height: 48px;
    padding: 0 20px;
    border: 1px solid transparent;
    background: var(--background-contrast-info);
    color: inherit;
    font: inherit;
    cursor: pointer;
  }
  .onglets button.actif {
    border-color: var(--border-default-grey);
    border-bottom-color: var(--background-default-grey);
    background: var(--background-default-grey);
    box-shadow: inset 0 2px 0 var(--border-action-high-blue-france, #8585f6);
    color: var(--text-action-high-blue-france, #8585f6);
    font-weight: 700;
  }
  .panneau {
    display: flex;
    flex-direction: column;
    gap: 24px;
    border: 1px solid var(--border-default-grey);
    padding: 32px;
  }
  .choix-source {
    display: flex;
    flex-wrap: wrap;
    gap: 8px 24px;
    border: 0;
    padding: 0;
    margin: 0;
  }
  .choix-source legend {
    margin-bottom: 8px;
    font-weight: 700;
  }
  .choix-source label {
    display: inline-flex;
    align-items: center;
    gap: 8px;
  }
  .message {
    max-width: 1232px;
    margin: 40px auto;
    padding: 0 16px;
  }
  @media (max-width: 600px) {
    .page {
      padding-top: 28px;
    }
    .cartes-produits {
      grid-template-columns: 1fr;
      gap: 16px;
    }
    .carte-produit {
      min-height: 180px;
      padding: 24px;
    }
    .panneau {
      padding: 24px 16px;
    }
    .titre-page h1 {
      align-items: flex-start;
      flex-direction: column;
      gap: 8px;
    }
    .entete-interieur {
      gap: 12px;
    }
    .actions {
      margin-left: 0;
    }
  }
</style>
