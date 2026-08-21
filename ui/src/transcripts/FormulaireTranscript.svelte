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
  let guideOuvert = $state(false);
  let donneesVerifiees = $state(false);
  let dialog = $state<HTMLDialogElement | null>(null);

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
        if (!identiteId) identiteId = NOUVEAU;
        if (!produitId) produitId = NOUVEAU;
      })
      .catch((e) => {
        erreur = e instanceof Error ? e.message : 'Erreur lors du chargement';
      });
  });

  $effect(() => {
    if (!id) return;
    obtenirTranscript(id)
      .then((t) => {
        identiteId = String(t.identite_id);
        produitId = String(t.produit_id);
        dateEntretien = t.date_entretien;
        contenu = t.contenu;
      })
      .catch((e) => {
        erreur =
          e instanceof Error
            ? e.message
            : "Erreur lors du chargement de l'entretien";
      });
  });

  $effect(() => {
    if (!dialog) return;
    if (guideOuvert) dialog.showModal();
    else dialog.close();
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
    donneesVerifiees = false;
    guideOuvert = true;
  }

  async function enregistrer() {
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
      onnaviquer({ nom: 'sources:entretiens' });
    } catch {
      erreur = 'Une erreur est survenue, veuillez réessayer.';
    }
  }
</script>

<div class="fr-container fr-py-4w">
  <nav class="fr-breadcrumb" aria-label="vous êtes ici :">
    <ol class="fr-breadcrumb__list">
      <li>
        <a class="fr-breadcrumb__link" href="#sources/entretiens">
          Entretiens utilisateurs
        </a>
      </li>
      <li><span aria-current="page">{id ? 'Modifier' : 'Ajouter'}</span></li>
    </ol>
  </nav>

  <h1 class="fr-h2">{id ? "Modifier l'entretien" : 'Ajouter un entretien'}</h1>

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
      label="Contenu de l'entretien"
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
      <button
        class="fr-btn fr-btn--secondary"
        type="button"
        onclick={() => onnaviquer({ nom: 'sources:entretiens' })}>Annuler</button
      >
      <button class="fr-btn" type="submit">
        {id ? 'Enregistrer les modifications' : "Enregistrer l'entretien"}
      </button>
    </div>
  </form>
</div>

<dialog
  bind:this={dialog}
  class="fr-modal"
  aria-labelledby="guide-confidentialite-titre"
  onclose={() => (guideOuvert = false)}
>
  <div class="fr-container fr-container--fluid fr-container-md">
    <div class="fr-grid-row fr-grid-row--center">
      <div class="fr-col-12 fr-col-md-8 fr-col-lg-7">
        <div class="fr-modal__body">
          <div class="fr-modal__header">
            <button
              class="fr-btn--close fr-btn"
              type="button"
              onclick={() => (guideOuvert = false)}
            >
              Fermer
            </button>
          </div>
          <div class="fr-modal__content">
            <h1 id="guide-confidentialite-titre" class="fr-modal__title">
              Vérifiez le transcript avant de l’enregistrer
            </h1>
            <p>
              Les informations saisies seront enregistrées dans la base de données.
              Ne transmettez que des données préparées pour cet usage.
            </p>
            <h2 class="fr-h6">Guide de préparation</h2>
            <ol>
              <li>
                <strong>Anonymisez les personnes et les organisations.</strong> Remplacez
                les noms, adresses e-mail, numéros de téléphone, noms d’entreprise et tout
                élément permettant d’identifier quelqu’un par un terme générique, comme
                « une participante » ou « une collectivité ».
              </li>
              <li>
                <strong>Désensibilisez le contenu.</strong> Retirez les identifiants, liens
                internes, données d’accès, informations de sécurité, données personnelles
                et tout détail qui ne serait pas nécessaire pour comprendre le besoin exprimé.
              </li>
              <li>
                <strong>Généralisez les technologies et les produits.</strong> Ne citez
                aucun nom de logiciel, de service, d’équipement ou de produit. Utilisez
                par exemple « un outil de visioconférence » ou « une solution métier ».
                Ces précisions pourraient faciliter une attaque ciblée.
              </li>
            </ol>
            <p>
              Appliquez ces vérifications au contenu de l’entretien, ainsi qu’aux
              champs « Identité » et « Projet » si vous en créez de nouveaux.
            </p>
            <div class="fr-checkbox-group">
              <input
                id="donnees-verifiees"
                type="checkbox"
                bind:checked={donneesVerifiees}
              />
              <label class="fr-label" for="donnees-verifiees">
                Je confirme avoir anonymisé et désensibilisé les données, et retiré
                les noms de technologies et de produits.
              </label>
            </div>
          </div>
          <div class="fr-modal__footer">
            <ul
              class="fr-btns-group fr-btns-group--right fr-btns-group--inline-reverse fr-btns-group--inline-lg"
            >
              <li>
                <button
                  class="fr-btn fr-btn--secondary"
                  type="button"
                  onclick={() => (guideOuvert = false)}
                >
                  Revenir au formulaire
                </button>
              </li>
              <li>
                <button
                  class="fr-btn"
                  type="button"
                  disabled={!donneesVerifiees}
                  onclick={enregistrer}
                >
                  Enregistrer le transcript
                </button>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  </div>
</dialog>

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
