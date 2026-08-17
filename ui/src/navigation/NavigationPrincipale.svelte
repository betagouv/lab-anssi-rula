<script lang="ts">
  import type { Vue } from '../types';
  import { hashDepuisVue } from './routage';

  let { vue }: { vue: Vue } = $props();

  const dansSources = $derived(
    vue.nom.startsWith('sources:') || vue.nom === 'analyses'
  );

  const sousNavigation = {
    sources: [
      { label: 'Entretiens utilisateurs', vue: { nom: 'sources:entretiens' } },
      { label: 'Retours BizDev', vue: { nom: 'sources:retours-bizdev' } },
      { label: 'Demandes FeatureBase', vue: { nom: 'sources:featurebase' } },
    ],
  } as const;

  function estActif(cible: Vue): boolean {
    if (cible.nom === 'sources:entretiens') {
      return vue.nom.startsWith('sources:entretiens');
    }
    return vue.nom === cible.nom;
  }
</script>

<header class="fr-header">
  <div class="fr-header__body">
    <div class="fr-container">
      <div class="fr-header__body-row">
        <div class="fr-header__brand">
          <div class="fr-header__brand-top">
            <div class="fr-header__logo">
              <p class="fr-logo">République<br />Française</p>
            </div>
          </div>
          <div class="fr-header__service">
            <p class="fr-header__service-title">RULA</p>
            <p class="fr-header__service-tagline">
              Gestion des entretiens utilisateurs
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>
  <div class="fr-header__menu">
    <div class="fr-container">
      <nav class="fr-nav" aria-label="Menu principal">
        <ul class="fr-nav__list">
          <li class="fr-nav__item">
            <a
              href={hashDepuisVue({ nom: 'sources:entretiens' })}
              class="fr-nav__link"
              aria-current={dansSources ? 'page' : undefined}
            >
              Données sources
            </a>
          </li>
          <li class="fr-nav__item">
            <a
              href={hashDepuisVue({ nom: 'besoins' })}
              class="fr-nav__link"
              aria-current={vue.nom === 'besoins' ? 'page' : undefined}
            >
              Analyse des besoins
            </a>
          </li>
          <li class="fr-nav__item">
            <a
              href={hashDepuisVue({ nom: 'correspondances' })}
              class="fr-nav__link"
              aria-current={vue.nom === 'correspondances' ? 'page' : undefined}
            >
              Correspondances
            </a>
          </li>
        </ul>
      </nav>
      {#if dansSources}
        <nav class="navigation-secondaire" aria-label="Navigation de section">
          <ul>
            {#each sousNavigation.sources as item (item.label)}
              <li>
                <a
                  href={hashDepuisVue(item.vue)}
                  aria-current={estActif(item.vue) ? 'page' : undefined}
                  >{item.label}</a
                >
              </li>
            {/each}
          </ul>
        </nav>
      {/if}
    </div>
  </div>
</header>

<style>
  .navigation-secondaire {
    border-top: 1px solid var(--border-default-grey, #ddd);
    padding: 0.75rem 0;
  }

  .navigation-secondaire ul {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem 1.5rem;
    list-style: none;
    margin: 0;
    padding: 0;
  }

  .navigation-secondaire a {
    color: var(--text-action-high-blue-france, #000091);
    display: inline-block;
    padding: 0.5rem 0;
    text-decoration: none;
  }

  .navigation-secondaire a[aria-current='page'] {
    font-weight: 700;
    text-decoration: underline;
    text-underline-offset: 0.25rem;
  }
</style>
