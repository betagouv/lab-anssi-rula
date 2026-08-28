<script lang="ts">
  import { onMount } from 'svelte';
  import {
    listerProduits,
    listerProjets,
    obtenirProjet,
    type Produit,
    type Projet,
  } from './api/projets';
  import Entete from './mvp/Entete.svelte';
  import Entree from './mvp/Entree.svelte';
  import Dashboard from './mvp/Dashboard.svelte';
  import ListeProjets from './mvp/ListeProjets.svelte';
  import NouveauProjet from './mvp/NouveauProjet.svelte';
  import ProjetVue from './mvp/Projet.svelte';
  import Scan from './mvp/Scan.svelte';
  import Detail from './mvp/Detail.svelte';
  import { routeMvp } from './mvp/routage';
  import ListeRetoursBizDev from './retours/ListeRetoursBizDev.svelte';
  import DetailRetourBizDev from './retours/DetailRetourBizDev.svelte';
  import ListeFonctionnalites from './fonctionnalites/ListeFonctionnalites.svelte';
  import DetailFeatureBase from './fonctionnalites/DetailFeatureBase.svelte';
  import { vueDepuisHash } from './navigation/routage';

  let produits = $state<Produit[]>([]);
  let projets = $state<Projet[]>([]);
  let projet = $state<Projet | null>(null);
  let erreur = $state('');
  let hash = $state('');
  const route = $derived(routeMvp(hash));
  const produitId = $derived(
    route && 'produitId' in route ? route.produitId : undefined
  );
  const produit = $derived(produits.find((item) => item.id === produitId));
  const produitEntete = $derived(
    route && 'projetId' in route
      ? produits.find((item) => item.id === projet?.produit_id)?.nom
      : produit?.nom
  );
  const ancienneVue = $derived(vueDepuisHash(hash));

  async function charger() {
    try {
      produits = await listerProduits();
      hash = window.location.hash;
      if (route && 'produitId' in route)
        projets = await listerProjets(route.produitId);
      if (route && 'projetId' in route) projet = await obtenirProjet(route.projetId);
    } catch (e) {
      erreur = e instanceof Error ? e.message : 'Erreur de chargement';
    }
  }

  onMount(() => {
    void charger();
    window.addEventListener('hashchange', charger);
    return () => window.removeEventListener('hashchange', charger);
  });

  const versProjet = (id: number) => (window.location.hash = `#/projets/${id}`);
  const versScan = () => (window.location.hash = `#/projets/${projet?.id}/scan`);
  const versDetail = () => (window.location.hash = `#/projets/${projet?.id}/detail`);
</script>

<Entete produit={produitEntete} />
{#if erreur}
  <main class="erreur">{erreur}</main>
{:else if !produits.length}
  <main class="chargement">Chargement…</main>
{:else if route?.nom === 'entree'}
  <Entree {produits} />
{:else if ancienneVue.nom === 'sources:retours-bizdev'}
  <ListeRetoursBizDev />
{:else if ancienneVue.nom === 'sources:retours-bizdev:detail'}
  <DetailRetourBizDev id={ancienneVue.id} />
{:else if ancienneVue.nom === 'sources:featurebase'}
  <ListeFonctionnalites />
{:else if ancienneVue.nom === 'sources:featurebase:detail'}
  <DetailFeatureBase id={ancienneVue.id} />
{:else if route?.nom === 'dashboard' && produit}
  <Dashboard {produit} {projets} />
{:else if route?.nom === 'projets' && produit}
  <ListeProjets {produit} {projets} />
{:else if route?.nom === 'nouveau' && produit}
  <NouveauProjet {produit} oncree={versProjet} />
{:else if projet && route?.nom === 'projet'}
  <ProjetVue {projet} onscan={versScan} />
{:else if projet && route?.nom === 'scan'}
  <Scan {projet} onvalide={versDetail} />
{:else if projet && route?.nom === 'detail'}
  <Detail {projet} />
{:else}
  <main class="erreur">Page introuvable.</main>
{/if}

<style>
  :global(body) {
    margin: 0;
    color: var(--text-default-grey);
    font-family: Marianne, Arial, sans-serif;
  }
  .chargement,
  .erreur {
    margin: 3rem auto;
    max-width: 1200px;
    padding: 0 1.5rem;
  }
  .erreur {
    color: #ce0500;
  }
</style>
