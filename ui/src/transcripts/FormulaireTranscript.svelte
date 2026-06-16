<script lang="ts">
  import type { Vue } from '../types';
  import {
    obtenirTranscript,
    ajouterTranscript,
    modifierTranscript,
  } from '../api/transcripts';

  const NOUVEAU = '__nouveau__';

  type Option = { value: string; label: string };
  type Ressource = { id: number; nom: string };

  let { id = undefined, onnaviquer }: { id?: number; onnaviquer: (v: Vue) => void } =
    $props();

  let identites = $state<Option[]>([]);
  let produits = $state<Option[]>([]);
  let identiteId = $state('');
  let nouvelleIdentite = $state('');
  let produitId = $state('');
  let nouveauProduit = $state('');
  let dateEntretien = $state('');
  let contenu = $state('');
  let erreur = $state('');

  function versOptions(ressources: Ressource[], libelle: string): Option[] {
    return [
      { value: NOUVEAU, label: libelle },
      ...ressources.map((r) => ({ value: String(r.id), label: r.nom })),
    ];
  }

  $effect(() => {
    Promise.all([fetch('/api/identites'), fetch('/api/produits')])
      .then(([ri, rp]) =>
        Promise.all([
          ri.json() as Promise<Ressource[]>,
          rp.json() as Promise<Ressource[]>,
        ])
      )
      .then(([ids, prods]) => {
        identites = versOptions(ids, '+ Nouvelle identité');
        produits = versOptions(prods, '+ Nouveau projet');
      });
  });

  $effect(() => {
    if (!id) return;
    obtenirTranscript(id).then((t) => {
      identiteId = String(t.identite_id);
      produitId = String(t.produit_id);
      dateEntretien = t.date_entretien;
      contenu = t.contenu;
    });
  });

  async function creerSiNouveau(
    valeur: string,
    nom: string,
    route: string
  ): Promise<number> {
    if (valeur !== NOUVEAU) return Number(valeur);
    const r = await fetch(route, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ nom }),
    });
    return ((await r.json()) as { id: number }).id;
  }

  async function soumettre(e: SubmitEvent) {
    e.preventDefault();
    erreur = '';
    try {
      const [iId, pId] = await Promise.all([
        creerSiNouveau(identiteId, nouvelleIdentite, '/api/identites'),
        creerSiNouveau(produitId, nouveauProduit, '/api/produits'),
      ]);
      const payload = {
        identite_id: iId,
        produit_id: pId,
        date_entretien: dateEntretien,
        contenu,
      };
      await (id ? modifierTranscript(id, payload) : ajouterTranscript(payload));
      onnaviquer({ nom: 'transcripts:liste' });
    } catch {
      erreur = 'Une erreur est survenue, veuillez réessayer.';
    }
  }
</script>

<div class="fr-container fr-py-4w">
  <nav class="fr-breadcrumb" aria-label="vous êtes ici :">
    <ol class="fr-breadcrumb__list">
      <li>
        <a
          href="#transcripts"
          class="fr-breadcrumb__link"
          onclick={(e) => {
            e.preventDefault();
            onnaviquer({ nom: 'transcripts:liste' });
          }}
        >
          Transcripts
        </a>
      </li>
      <li><span aria-current="page">{id ? 'Modifier' : 'Ajouter'}</span></li>
    </ol>
  </nav>

  <h1 class="fr-h2">{id ? 'Modifier le transcript' : 'Ajouter un transcript'}</h1>

  <form onsubmit={soumettre}>
    <dsfr-select
      id="identite"
      label="Identité"
      options={identites}
      value={identiteId}
      required="true"
      onvaluechanged={(e) => {
        identiteId = e.detail;
      }}
    ></dsfr-select>
    {#if identiteId === NOUVEAU}
      <dsfr-input
        id="nouvelle-identite"
        label="Nom de la nouvelle identité"
        type="text"
        value={nouvelleIdentite}
        required="true"
        onvaluechanged={(e) => {
          nouvelleIdentite = e.detail;
        }}
      ></dsfr-input>
    {/if}

    <dsfr-input
      id="date-entretien"
      label="Date de l'entretien"
      type="date"
      value={dateEntretien}
      required="true"
      onvaluechanged={(e) => {
        dateEntretien = e.detail;
      }}
    ></dsfr-input>

    <dsfr-select
      id="produit"
      label="Projet"
      options={produits}
      value={produitId}
      required="true"
      onvaluechanged={(e) => {
        produitId = e.detail;
      }}
    ></dsfr-select>
    {#if produitId === NOUVEAU}
      <dsfr-input
        id="nouveau-produit"
        label="Nom du nouveau projet"
        type="text"
        value={nouveauProduit}
        required="true"
        onvaluechanged={(e) => {
          nouveauProduit = e.detail;
        }}
      ></dsfr-input>
    {/if}

    <dsfr-textarea
      id="contenu"
      label="Transcript"
      value={contenu}
      rows="12"
      required="true"
      onvaluechanged={(e) => {
        contenu = e.detail;
      }}
    ></dsfr-textarea>

    {#if erreur}
      <p class="erreur">{erreur}</p>
    {/if}

    <div class="boutons">
      <dsfr-button
        label="Annuler"
        kind="secondary"
        type="button"
        onclick={() => onnaviquer({ nom: 'transcripts:liste' })}
      ></dsfr-button>
      <dsfr-button
        label={id ? 'Enregistrer les modifications' : 'Enregistrer le transcript'}
        type="submit"
      ></dsfr-button>
    </div>
  </form>
</div>

<style>
  form {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
    max-width: 720px;
  }
  .boutons {
    display: flex;
    gap: 1rem;
  }
  .erreur {
    color: var(--error-425-625, #ce0500);
  }
</style>
