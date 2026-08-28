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
  import AjouterSource from './mvp/AjouterSource.svelte';
  import ProjetVue from './mvp/Projet.svelte';
  import Scan from './mvp/Scan.svelte';
  import ConfigurationAnalyse from './mvp/ConfigurationAnalyse.svelte';
  import EtapeAnalyse from './mvp/EtapeAnalyse.svelte';
  import Detail from './mvp/Detail.svelte';
  import EntretienLecture from './mvp/EntretienLecture.svelte';
  import { routeMvp } from './mvp/routage';
  import ListeRetoursBizDev from './retours/ListeRetoursBizDev.svelte';
  import DetailRetourBizDev from './retours/DetailRetourBizDev.svelte';
  import ListeFonctionnalites from './fonctionnalites/ListeFonctionnalites.svelte';
  import DetailFeatureBase from './fonctionnalites/DetailFeatureBase.svelte';
  import ListeAnalyses from './analyses/ListeAnalyses.svelte';
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
  const projetProduit = $derived(
    projet ? produits.find((item) => item.id === projet?.produit_id) : undefined
  );
  const produitEntete = $derived(
    route && 'projetId' in route
      ? produits.find((item) => item.id === projet?.produit_id)?.nom
      : produit?.nom
  );
  const ancienneVue = $derived(vueDepuisHash(hash));

  async function charger() {
    try {
      produits = await listerProduits();
      const nouvelleRoute = routeMvp(window.location.hash);
      hash = window.location.hash;
      if (nouvelleRoute && 'produitId' in nouvelleRoute)
        projets = await listerProjets(nouvelleRoute.produitId);
      if (nouvelleRoute && 'projetId' in nouvelleRoute)
        projet = await obtenirProjet(nouvelleRoute.projetId);
      else projet = null;
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
  const versDetail = () => (window.location.hash = `#/projets/${projet?.id}/detail`);
  const versEtapeSuivante = (cle: string) => {
    const suivante: Record<string, string> = {
      'scan-neutre': 'points-a-retenir',
      'points-a-retenir': 'thematisation',
    };
    window.location.hash = suivante[cle]
      ? `#/projets/${projet?.id}/analyse/${suivante[cle]}`
      : `#/projets/${projet?.id}/detail`;
  };
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
{:else if ancienneVue.nom === 'analyses'}
  <ListeAnalyses />
{:else if route?.nom === 'dashboard' && produit}
  <Dashboard {produit} {projets} />
{:else if route?.nom === 'projets' && produit}
  <ListeProjets {produit} {projets} />
{:else if route?.nom === 'nouveau' && produit}
  <NouveauProjet {produit} oncree={versProjet} />
{:else if route?.nom === 'source' && produit && route.source}
  <AjouterSource {produit} source={route.source} />
{:else if route?.nom === 'source-liste' && route.source === 'bizdev'}
  <ListeRetoursBizDev produitInitialId={route.produitId} />
{:else if route?.nom === 'source-liste' && route.source === 'featurebase'}
  <ListeFonctionnalites produitInitialId={route.produitId} />
{:else if route?.nom === 'entretien' && projet}
  <EntretienLecture {projet} entretienId={route.entretienId} />
{:else if route?.nom === 'source-projet' && projet && projetProduit}
  <AjouterSource
    produit={projetProduit}
    source={route.source}
    projetInitialId={projet.id}
  />
{:else if projet && route?.nom === 'projet'}
  <ProjetVue {projet} produitNom={produitEntete} />
{:else if projet && route?.nom === 'configuration'}
  <ConfigurationAnalyse
    {projet}
    onlance={() =>
      (window.location.hash = `#/projets/${projet?.id}/analyse/scan-neutre`)}
  />
{:else if projet && route?.nom === 'analyse'}
  <EtapeAnalyse
    {projet}
    cle={route.etape ?? 'scan-neutre'}
    onvalide={() => versEtapeSuivante(route.etape ?? 'scan-neutre')}
  />
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
