<script lang="ts">
  import { onMount } from 'svelte';

  const NOUVEAU = '__nouveau__';

  type Option = { value: string; label: string };
  type Ressource = { id: number; nom: string };

  let identites = $state<Option[]>([]);
  let produits = $state<Option[]>([]);
  let identiteId = $state('');
  let nouvelleIdentite = $state('');
  let produitId = $state('');
  let nouveauProduit = $state('');
  let dateEntretien = $state('');
  let contenu = $state('');
  let succes = $state(false);
  let erreur = $state('');

  function versOptions(ressources: Ressource[], libelle: string): Option[] {
    return [
      { value: NOUVEAU, label: libelle },
      ...ressources.map((r) => ({ value: String(r.id), label: r.nom })),
    ];
  }

  async function chargerOptions() {
    const [ri, rp] = await Promise.all([
      fetch('/api/identites'),
      fetch('/api/produits'),
    ]);
    identites = versOptions(await ri.json(), '+ Nouvelle identité');
    produits = versOptions(await rp.json(), '+ Nouveau projet');
  }

  onMount(chargerOptions);

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
    return (await r.json()).id;
  }

  async function soumettre(e: SubmitEvent) {
    e.preventDefault();
    erreur = '';
    try {
      const [iId, pId] = await Promise.all([
        creerSiNouveau(identiteId, nouvelleIdentite, '/api/identites'),
        creerSiNouveau(produitId, nouveauProduit, '/api/produits'),
      ]);
      await fetch('/api/transcripts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          identite_id: iId,
          produit_id: pId,
          date_entretien: dateEntretien,
          contenu,
        }),
      });
      succes = true;
      await chargerOptions();
    } catch {
      erreur = 'Une erreur est survenue, veuillez réessayer.';
    }
  }

  function recommencer() {
    succes = false;
    identiteId = '';
    nouvelleIdentite = '';
    produitId = '';
    nouveauProduit = '';
    dateEntretien = '';
    contenu = '';
  }
</script>

{#if succes}
  <p class="confirmation">Transcript enregistré.</p>
  <dsfr-button
    label="Ajouter un autre transcript"
    kind="secondary"
    onclick={recommencer}
  ></dsfr-button>
{:else}
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

    <dsfr-button label="Enregistrer le transcript" type="submit"></dsfr-button>
  </form>
{/if}

<style>
  form {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
    max-width: 720px;
  }
  .confirmation {
    color: var(--green-emeraude-main-632, #00a95f);
    font-weight: 700;
  }
  .erreur {
    color: var(--error-425-625, #ce0500);
  }
</style>
