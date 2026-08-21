<script lang="ts">
  import type { Vue } from '../types';
  import {
    obtenirTranscript,
    ajouterTranscript,
    modifierTranscript,
    TranscriptNonConforme,
    type RaisonRefusTranscript,
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
  let raisonsRefus = $state<RaisonRefusTranscript[]>([]);
  let guideOuvert = $state(false);
  let donneesVerifiees = $state(false);
  let guide = $state<HTMLElement | null>(null);
  let verificationEnCours = $state(false);

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
    if (!guideOuvert || !guide) return;
    guide.focus();
    guide.scrollIntoView({ behavior: 'smooth', block: 'start' });
  });

  function demanderEnregistrement() {
    donneesVerifiees = false;
    raisonsRefus = [];
    erreur = '';
    guideOuvert = true;
  }

  async function enregistrer() {
    erreur = '';
    raisonsRefus = [];
    verificationEnCours = true;
    try {
      const payload = {
        ...(identiteId === NOUVEAU
          ? { nouvelle_identite: nouvelleIdentite }
          : { identite_id: Number(identiteId) }),
        ...(produitId === NOUVEAU
          ? { nouveau_produit: nouveauProduit }
          : { produit_id: Number(produitId) }),
        date_entretien: dateEntretien,
        contenu,
      };
      await (id ? modifierTranscript(id, payload) : ajouterTranscript(payload));
      onnaviquer({ nom: 'sources:entretiens' });
    } catch (e) {
      if (e instanceof TranscriptNonConforme) {
        raisonsRefus = e.raisons;
      } else {
        erreur =
          'La vérification des données est indisponible. Le transcript n’a pas été enregistré.';
      }
    } finally {
      verificationEnCours = false;
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

  <form>
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

    {#if guideOuvert}
      <section
        bind:this={guide}
        class="guide fr-alert fr-alert--info"
        aria-labelledby="guide-confidentialite-titre"
        tabindex="-1"
      >
        <h2 id="guide-confidentialite-titre" class="fr-h5">
          Vérifiez le transcript avant de l’enregistrer
        </h2>
        <p>
          Les informations saisies seront enregistrées dans la base de données. Ne
          transmettez que des données préparées pour cet usage.
        </p>
        <h3 class="fr-h6">Guide de préparation</h3>
        <ol>
          <li>
            <strong>Anonymisez les personnes et les organisations.</strong> Remplacez les
            noms, adresses e-mail, numéros de téléphone, noms d’entreprise et tout élément
            permettant d’identifier quelqu’un par un terme générique, comme « une participante
            » ou « une collectivité ».
          </li>
          <li>
            <strong>Désensibilisez le contenu.</strong> Retirez les identifiants, liens
            internes, données d’accès, informations de sécurité, données personnelles et
            tout détail qui ne serait pas nécessaire pour comprendre le besoin exprimé.
          </li>
          <li>
            <strong>Généralisez les technologies et les produits.</strong> Ne citez aucun
            nom de logiciel, de service, d’équipement ou de produit. Utilisez par exemple
            « un outil de visioconférence » ou « une solution métier ». Ces précisions
            pourraient faciliter une attaque ciblée.
          </li>
        </ol>
        <p>
          Appliquez ces vérifications au contenu de l’entretien, ainsi qu’aux champs
          « Identité » et « Projet » si vous en créez de nouveaux.
        </p>
        <div class="fr-checkbox-group">
          <input
            id="donnees-verifiees"
            type="checkbox"
            bind:checked={donneesVerifiees}
          />
          <label class="fr-label" for="donnees-verifiees">
            Je confirme avoir anonymisé et désensibilisé les données, et retiré les
            noms de technologies et de produits.
          </label>
        </div>
      </section>
    {/if}

    {#if raisonsRefus.length}
      <div class="fr-alert fr-alert--error">
        <h2 class="fr-alert__title">Transcript non enregistré</h2>
        <p>
          Les données ne semblent pas suffisamment anonymisées ou désensibilisées.
          Corrigez les éléments signalés avant de réessayer.
        </p>
        <ul>
          {#each raisonsRefus as raison (`${raison.categorie}-${raison.element}`)}
            <li>{raison.element} : {raison.raison}</li>
          {/each}
        </ul>
      </div>
    {:else if erreur}
      <p class="erreur">{erreur}</p>
    {/if}

    <div class="boutons">
      <button
        class="fr-btn fr-btn--secondary"
        type="button"
        onclick={() => onnaviquer({ nom: 'sources:entretiens' })}>Annuler</button
      >
      {#if guideOuvert}
        <button
          class="fr-btn fr-btn--secondary"
          type="button"
          onclick={() => (guideOuvert = false)}>Revenir au formulaire</button
        >
        <button
          class="fr-btn"
          type="button"
          disabled={!donneesVerifiees || verificationEnCours}
          onclick={enregistrer}
          >{verificationEnCours
            ? 'Vérification en cours…'
            : 'Enregistrer le transcript'}</button
        >
      {:else}
        <button class="fr-btn" type="button" onclick={demanderEnregistrement}>
          {id ? 'Enregistrer les modifications' : "Enregistrer l'entretien"}
        </button>
      {/if}
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
  .guide {
    margin: 0;
  }
  .boutons {
    display: flex;
    flex-wrap: wrap;
    gap: 1rem;
  }
  .erreur {
    color: var(--error-425-625, #ce0500);
  }
</style>
