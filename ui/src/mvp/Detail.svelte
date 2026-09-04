<script lang="ts">
  import { marked } from 'marked';
  import {
    obtenirDetailAnalyse,
    listerEntretiens,
    type Entretien,
    type Projet,
  } from '../api/projets';
  import ProgressionAnalyse from './ProgressionAnalyse.svelte';
  let { projet }: { projet: Projet } = $props();
  let sorties = $state<{ cle: string; libelle: string; contenu: string }[]>([]);
  let entretiens = $state<Entretien[]>([]);
  let erreur = $state('');
  $effect(() => {
    Promise.all([obtenirDetailAnalyse(projet.id), listerEntretiens(projet.id)])
      .then(([analyse, entretiensProjet]) => {
        sorties = analyse.etapes;
        entretiens = entretiensProjet;
      })
      .catch(
        (e) => (erreur = e instanceof Error ? e.message : 'Erreur de chargement')
      );
  });
</script>

<main class="detail">
  <section>
    <a href={`#/produits/${projet.produit_id}/projets`}>← Projets</a>
    <ProgressionAnalyse courant={6} />
    <h1>Détail analyse</h1>
    {#if erreur}<p class="erreur" role="alert">{erreur}</p>{/if}
    <p>Nom du projet de recherche</p>
    <h2>{projet.nom}</h2>
    {#each sorties as sortie (sortie.cle)}
      <article>
        <h2>{sortie.libelle}</h2>
        <!-- eslint-disable-next-line svelte/no-at-html-tags -->
        {@html marked.parse(sortie.contenu)}
      </article>
    {:else}<p>Aucune étape validée pour le moment.</p>{/each}
  </section>
  <aside>
    <h2>Données brutes</h2>
    {#each entretiens as entretien (entretien.id)}<details>
        <summary>Entretien de {entretien.participant}</summary>
        <p>{entretien.contenu}</p>
        <p>{entretien.note_moderateur}</p>
      </details>{/each}
  </aside>
</main>

<style>
  .detail {
    display: grid;
    grid-template-columns: minmax(0, 2fr) minmax(18rem, 1fr);
    min-height: calc(100dvh - 6rem);
  }
  section {
    padding: 2.5rem max(1.5rem, calc((100vw - 1200px) / 2));
    padding-right: 3rem;
  }
  aside {
    border-left: 1px solid var(--border-default-grey);
    padding: 2.5rem 2rem;
  }
  h1 {
    font-size: clamp(2rem, 3vw, 2.7rem);
    margin: 2rem 0 1rem;
  }
  h2 {
    font-size: clamp(1.4rem, 2.3vw, 2rem);
  }
  article {
    margin-top: 3rem;
    line-height: 1.5;
  }
  article :global(h2),
  article :global(h3) {
    margin: 1.5rem 0 0.75rem;
  }
  article :global(p) {
    margin: 0.75rem 0;
  }
  article :global(ul),
  article :global(ol) {
    padding-left: 1.5rem;
  }
  article :global(table) {
    border-collapse: collapse;
    display: block;
    max-width: 100%;
    overflow-x: auto;
    width: max-content;
  }
  article :global(th),
  article :global(td) {
    border: 1px solid var(--border-default-grey);
    padding: 0.75rem 1rem;
    text-align: left;
    vertical-align: top;
  }
  article :global(th) {
    background: var(--background-alt-grey);
  }
  details {
    border-bottom: 1px solid var(--border-default-grey);
    padding: 1.25rem 0;
  }
  summary {
    font-size: 1.1rem;
  }
  a {
    color: var(--text-action-high-blue-france);
  }
  .erreur {
    color: var(--text-default-error);
  }
  @media (max-width: 48rem) {
    .detail {
      grid-template-columns: 1fr;
    }
    aside {
      border-left: 0;
      border-top: 1px solid var(--border-default-grey);
    }
    section {
      padding-right: 1.5rem;
    }
  }
</style>
