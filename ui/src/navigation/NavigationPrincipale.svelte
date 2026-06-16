<script lang="ts">
  import type { Vue } from '../types';

  let { vue, onnaviquer }: { vue: Vue; onnaviquer: (v: Vue) => void } = $props();

  const domaine = $derived(vue.nom.split(':')[0]);
</script>

<header class="fr-header" role="banner">
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
      <nav class="fr-nav" aria-label="Menu principal" role="navigation">
        <ul class="fr-nav__list">
          <li class="fr-nav__item">
            <button
              class="fr-nav__link"
              aria-current={domaine === 'transcripts' ? 'page' : undefined}
              onclick={() => onnaviquer({ nom: 'transcripts:liste' })}
            >
              Transcripts
            </button>
          </li>
          <li class="fr-nav__item">
            <button
              class="fr-nav__link"
              aria-current={domaine === 'analyses' ? 'page' : undefined}
              onclick={() => onnaviquer({ nom: 'analyses' })}
            >
              Analyses
            </button>
          </li>
        </ul>
      </nav>
    </div>
  </div>
</header>
