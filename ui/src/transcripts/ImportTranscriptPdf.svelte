<script lang="ts">
  import { onMount } from 'svelte';
  import {
    dureeDepuisSoumission,
    dureeLocale,
    libelleProgression,
    pourcentageProgression,
    type ProgressionPreparation,
  } from './progression';
  import {
    ErreurSuiviPreparation,
    lirePreparation,
    type ResultatPreparation,
  } from './suivi-preparation';
  import RelecturePseudonymisation from './RelecturePseudonymisation.svelte';
  import {
    initialiserEtatRelecture,
    type EtatRelecture,
    type OccurrenceSource,
  } from './modele-relecture';
  import ConfirmationPseudonymisation from './ConfirmationPseudonymisation.svelte';

  let {
    produitId,
    typeSource,
    onconfirme,
  }: {
    produitId: number;
    typeSource: 'produit' | 'bizdev';
    onconfirme?: () => void;
  } = $props();
  let fichier = $state<File | null>(null);
  let dateEntretien = $state('');
  let nomSource = $state('');
  let contenu = $state('');
  let contexte = $state('');
  let contenuOriginal = $state('');
  let contexteOriginal = $state('');
  let occurrences = $state<OccurrenceSource[]>([]);
  let etatRelecture = $state<EtatRelecture | undefined>();
  let locuteurs = $state<
    {
      identifiant: string;
      role: 'interne' | 'externe' | 'indetermine';
      justification: string;
      nom_affiche?: string;
    }[]
  >([]);
  let conflitsCategoriesFusionnes = $state(0);
  let problemes = $state<{ categorie: string; element: string; raison: string }[]>(
    []
  );
  let erreur = $state('');
  let enCours = $state(false);
  let progression = $state<ProgressionPreparation | null>(null);
  let jetonPreparation = $state<string | null>(null);
  let etatSynchronisation = $state<'enregistre' | 'en_attente' | 'echec'>(
    'enregistre'
  );
  let minuteurSauvegarde: ReturnType<typeof setTimeout> | null = null;
  let versionEtat = 0;
  let versionEnregistree = 0;
  let sauvegardeActive = false;
  let controleSuivi: AbortController | null = null;
  let controleEnvoi: AbortController | null = null;
  let timerHorloge: ReturnType<typeof setInterval> | null = null;
  let timerAttente: ReturnType<typeof setTimeout> | null = null;
  let resoudreAttente: (() => void) | null = null;
  let secondesServeur = 0;
  let horodatageServeur = 0;
  let monte = false;
  const clePreparation = $derived(`rula-preparation-${typeSource}-${produitId}`);

  function avertirAvantSortie(event: BeforeUnloadEvent) {
    if (versionEtat === versionEnregistree) return;
    event.preventDefault();
    event.returnValue = '';
  }

  function actualiserProgression(valeur: ProgressionPreparation) {
    progression = valeur;
    secondesServeur = valeur.duree_secondes;
    horodatageServeur = performance.now();
    timerHorloge ??= setInterval(() => {
      if (progression)
        progression = {
          ...progression,
          duree_secondes: dureeLocale(
            secondesServeur,
            horodatageServeur,
            performance.now()
          ),
        };
    }, 1000);
  }

  function arreterHorloge() {
    if (timerHorloge !== null) clearInterval(timerHorloge);
    timerHorloge = null;
  }

  function attendre(delai: number): Promise<void> {
    return new Promise((resoudre) => {
      resoudreAttente = resoudre;
      timerAttente = setTimeout(() => {
        timerAttente = null;
        resoudreAttente = null;
        resoudre();
      }, delai);
    });
  }

  function annulerAttente() {
    if (timerAttente !== null) clearTimeout(timerAttente);
    timerAttente = null;
    const terminer = resoudreAttente;
    resoudreAttente = null;
    terminer?.();
  }

  onMount(() => {
    monte = true;
    window.addEventListener('beforeunload', avertirAvantSortie);
    const preparationEnregistree = sessionStorage.getItem(clePreparation);
    if (preparationEnregistree && /^[0-9a-f]{32}$/.test(preparationEnregistree)) {
      jetonPreparation = preparationEnregistree;
      void suivrePreparation(preparationEnregistree);
    }
    return () => {
      monte = false;
      window.removeEventListener('beforeunload', avertirAvantSortie);
      if (minuteurSauvegarde !== null) clearTimeout(minuteurSauvegarde);
      controleEnvoi?.abort();
      controleSuivi?.abort();
      annulerAttente();
      arreterHorloge();
      contenuOriginal = '';
      contexteOriginal = '';
      occurrences = [];
    };
  });

  async function preparer() {
    if (!fichier || enCours || jetonPreparation) return;
    enCours = true;
    contenuOriginal = '';
    contexteOriginal = '';
    occurrences = [];
    etatRelecture = undefined;
    progression = null;
    arreterHorloge();
    erreur = '';
    conflitsCategoriesFusionnes = 0;
    let jeton: string | null = null;
    try {
      const donnees = new FormData();
      donnees.set('fichier', fichier);
      donnees.set('type_source', typeSource);
      donnees.set('produit_id', String(produitId));
      donnees.set('contexte', contexte);
      const controle = new AbortController();
      controleEnvoi = controle;
      const reponse = await fetch('/api/transcripts-pdf/preparation', {
        method: 'POST',
        body: donnees,
        signal: controle.signal,
      });
      const demande = await reponse.json();
      if (!monte) return;
      if (!reponse.ok) throw new Error(demande.detail ?? 'Préparation impossible.');
      const identifiant = String(demande.identifiant);
      jeton = identifiant;
      jetonPreparation = identifiant;
      sessionStorage.setItem(clePreparation, identifiant);
      actualiserProgression(demande.progression);
    } catch (cause) {
      if (!monte) return;
      erreur = cause instanceof Error ? cause.message : 'Préparation impossible.';
    } finally {
      controleEnvoi = null;
      if (monte) enCours = false;
    }
    if (jeton) await suivrePreparation(jeton, true);
  }

  async function suivrePreparation(
    jeton = jetonPreparation,
    attendreAvantPremierPoll = false
  ) {
    if (!jeton || enCours) return;
    enCours = true;
    erreur = '';
    try {
      if (attendreAvantPremierPoll) await attendre(2000);
      while (monte && jetonPreparation === jeton) {
        const controle = new AbortController();
        controleSuivi = controle;
        let resultat: ResultatPreparation;
        try {
          resultat = await lirePreparation(
            jeton,
            (url, signal) => fetch(url, { signal }),
            controle.signal
          );
        } finally {
          if (controleSuivi === controle) controleSuivi = null;
        }
        if (!monte) return;
        actualiserProgression(resultat.progression);
        if (resultat.statut === 'echec') {
          progression = { ...resultat.progression, phase: 'echec' };
          jetonPreparation = null;
          sessionStorage.removeItem(clePreparation);
          arreterHorloge();
          erreur = resultat.erreur;
          return;
        }
        if (resultat.statut === 'termine') {
          contenu = resultat.contenu;
          contexte = resultat.contexte;
          contenuOriginal = resultat.contenu_original;
          contexteOriginal = resultat.contexte_original;
          occurrences = resultat.occurrences;
          nomSource = resultat.nom_source;
          dateEntretien = resultat.date_entretien ?? '';
          locuteurs = resultat.locuteurs;
          etatRelecture = initialiserEtatRelecture(
            contenuOriginal,
            contexteOriginal,
            occurrences,
            resultat.etat_relecture
          );
          conflitsCategoriesFusionnes = resultat.conflits_categories_fusionnes;
          etatSynchronisation = 'enregistre';
          versionEnregistree = versionEtat;
          programmerSauvegarde();
          arreterHorloge();
          return;
        }
        await attendre(2000);
      }
    } catch (cause) {
      if (!monte) return;
      if (cause instanceof ErreurSuiviPreparation && cause.code === 'introuvable') {
        jetonPreparation = null;
        sessionStorage.removeItem(clePreparation);
        contenuOriginal = '';
        contexteOriginal = '';
        occurrences = [];
        etatRelecture = undefined;
        versionEnregistree = versionEtat;
        if (progression) progression = { ...progression, phase: 'echec' };
        arreterHorloge();
        erreur =
          'La préparation a expiré ou est introuvable. Réimportez le fichier.';
      } else {
        erreur =
          'Le suivi a été interrompu. Reprenez le suivi pour récupérer le résultat.';
      }
    } finally {
      if (monte) enCours = false;
    }
  }

  function programmerSauvegarde() {
    if (!jetonPreparation || !etatRelecture) return;
    versionEtat += 1;
    etatSynchronisation = 'en_attente';
    if (minuteurSauvegarde !== null) clearTimeout(minuteurSauvegarde);
    minuteurSauvegarde = setTimeout(() => void sauvegarderEtat(), 300);
  }

  async function sauvegarderEtat() {
    if (!jetonPreparation || !etatRelecture || sauvegardeActive) return;
    const identifiant = jetonPreparation;
    const version = versionEtat;
    sauvegardeActive = true;
    try {
      const reponse = await fetch(
        `/api/transcripts-pdf/preparation/${identifiant}/relecture`,
        {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            etat_relecture: etatRelecture,
            locuteurs: locuteurs.map(({ identifiant: id, role, nom_affiche }) => ({
              identifiant: id,
              role,
              nom_affiche: nom_affiche ?? '',
            })),
            date_entretien: dateEntretien || null,
          }),
        }
      );
      if (!reponse.ok) throw new Error('État de relecture non enregistré.');
      if (version === versionEtat) {
        versionEnregistree = version;
        etatSynchronisation = 'enregistre';
      }
    } catch {
      if (version === versionEtat) etatSynchronisation = 'echec';
    } finally {
      sauvegardeActive = false;
      if (version !== versionEtat) void sauvegarderEtat();
    }
  }

  async function abandonnerPreparation() {
    const identifiant = jetonPreparation;
    if (identifiant) {
      await fetch(`/api/transcripts-pdf/preparation/${identifiant}`, {
        method: 'DELETE',
      }).catch(() => undefined);
    }
    sessionStorage.removeItem(clePreparation);
    jetonPreparation = null;
    etatRelecture = undefined;
    contenuOriginal = '';
    contexteOriginal = '';
    occurrences = [];
    contenu = '';
    contexte = '';
    locuteurs = [];
    versionEtat += 1;
    versionEnregistree = versionEtat;
    etatSynchronisation = 'enregistre';
  }

  async function confirmer(): Promise<boolean> {
    if (!jetonPreparation) {
      erreur = 'La préparation a expiré. Réimportez le fichier pour confirmer.';
      return false;
    }
    enCours = true;
    progression = null;
    erreur = '';
    try {
      const reponse = await fetch('/api/transcripts-pdf', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          preparation_id: jetonPreparation,
          type_source: typeSource,
          nom_source: nomSource,
          produit_id: produitId,
          date_entretien: dateEntretien || null,
          contenu,
          contexte,
          locuteurs,
        }),
      });
      const resultat = await reponse.json();
      if (!reponse.ok) {
        if (resultat.detail?.problemes) problemes = resultat.detail.problemes;
        throw new Error(
          typeof resultat.detail === 'string'
            ? resultat.detail
            : 'Corrigez les éléments signalés avant de confirmer.'
        );
      }
      problemes = [];
      await abandonnerPreparation();
      contenuOriginal = '';
      contexteOriginal = '';
      occurrences = [];
      onconfirme?.();
      return true;
    } catch (cause) {
      erreur = cause instanceof Error ? cause.message : 'Enregistrement impossible.';
      return false;
    } finally {
      enCours = false;
    }
  }
</script>

<main class="contenu">
  <div class="etape">
    <p class="fr-text--sm">Étape 1 sur 2</p>
    <h2>Importer le transcript</h2>
    <div class="barres" aria-hidden="true">
      <span class:on={!contenuOriginal}></span><span
        class:on={Boolean(contenuOriginal)}
      ></span>
    </div>
    <p class="suite">Étape suivante : relire et valider la pseudonymisation</p>
  </div>
  {#if erreur}<p class="fr-alert fr-alert--error" role="alert">{erreur}</p>{/if}
  {#if !contenuOriginal}
    <section class="import">
      <div class="champ">
        <label class="fr-label" for="pdf">Transcript à pseudonymiser</label>
        <span class="fr-hint-text" id="pdf-aide"
          >Format PDF, 10 Mo maximum. Le fichier original n’est conservé que pendant
          la préparation.</span
        >
        <label
          class="depot"
          for="pdf"
          ondragover={(event) => event.preventDefault()}
          ondrop={(event) => {
            event.preventDefault();
            const depot = event.dataTransfer?.files[0];
            if (depot?.type === 'application/pdf') fichier = depot;
          }}
        >
          <span aria-hidden="true">⇧</span>
          {#if fichier}<strong>{fichier.name}</strong><span
              >{(fichier.size / 1024).toFixed(0)} Ko · PDF</span
            >
          {:else}<strong>Glissez-déposez votre fichier PDF ici</strong><span>ou</span
            ><span class="fr-btn fr-btn--secondary">Parcourir les fichiers</span
            >{/if}
          <input
            class="sr-only"
            id="pdf"
            name="fichier"
            type="file"
            accept=".pdf,application/pdf"
            aria-describedby="pdf-aide"
            onchange={(event) => {
              contenuOriginal = '';
              contexteOriginal = '';
              occurrences = [];
              contenu = '';
              fichier = event.currentTarget.files?.[0] ?? null;
            }}
          />
        </label>
      </div>
      <div class="champ">
        <label class="fr-label" for="contexte"
          >Contexte complémentaire <span class="optionnel">(facultatif)</span></label
        >
        <textarea class="fr-input" id="contexte" bind:value={contexte} rows="3"
        ></textarea>
      </div>
      <div class="actions-import">
        <button
          class="fr-btn"
          type="button"
          disabled={!fichier || enCours || jetonPreparation !== null}
          onclick={preparer}
          >{enCours ? 'Préparation…' : 'Pseudonymiser le transcript'}</button
        >
        <span>Vous relirez les éléments masqués avant l’enregistrement.</span>
      </div>
      {#if jetonPreparation && !enCours}
        <button
          class="fr-btn fr-btn--secondary"
          type="button"
          onclick={() => suivrePreparation()}>Reprendre la préparation</button
        >
      {/if}
      {#if progression && (enCours || jetonPreparation)}
        {@const pourcentage = pourcentageProgression(progression)}
        <section class="traitement" aria-label="Progression de la pseudonymisation">
          <h3>Pseudonymisation en cours</h3>
          <p class="fichier-nom">{fichier?.name ?? 'Préparation en cours'}</p>
          <div class="jauge-ligne">
            <strong>Progression</strong><strong
              >{pourcentage === null ? '…' : `${pourcentage} %`}</strong
            >
          </div>
          <div
            class="jauge"
            role="progressbar"
            aria-label="Progression de la préparation"
            aria-valuemin="0"
            aria-valuemax="100"
            aria-valuenow={pourcentage ?? undefined}
            aria-valuetext={pourcentage === null
              ? libelleProgression(progression)
              : `${progression.groupes_termines} groupes sur ${progression.groupes_total}`}
          >
            {#if pourcentage !== null}<div
                style={`width:${pourcentage}%`}
              ></div>{:else}<div class="indeterminee"></div>{/if}
          </div>
          <p class="temps">
            Temps écoulé depuis l’envoi : {dureeDepuisSoumission(
              progression.duree_secondes
            )}
          </p>
          <p class="temps" aria-live="polite">{libelleProgression(progression)}</p>
          {#if progression.phase === 'anonymisation' && progression.groupes_total !== null}<p
            >
              {progression.groupes_termines} groupe(s) sur {progression.groupes_total}
            </p>{/if}
        </section>
      {/if}
    </section>
  {:else}
    <section class="relecture-page">
      <div class="etape">
        <p class="fr-text--sm">Étape 2 sur 2</p>
        <h2>Relire et valider la pseudonymisation</h2>
        <div class="barres" aria-hidden="true">
          <span class="on"></span><span class="on"></span>
        </div>
      </div>
      <div class="relecture-tete">
        <div class="champ">
          <label class="fr-label" for="date-entretien">Date de l’entretien</label>
          <span class="fr-hint-text"
            >Préremplie à partir du nom du fichier quand elle est reconnue.</span
          >
          <input
            class="fr-input"
            id="date-entretien"
            type="date"
            bind:value={dateEntretien}
            oninput={programmerSauvegarde}
            required
          />
          {#if !dateEntretien}<span class="fr-error-text"
              >Renseignez la date pour pouvoir enregistrer.</span
            >{/if}
        </div>
        <p>
          Les éléments surlignés seront remplacés par leur libellé à
          l’enregistrement. Cliquez sur un élément pour afficher son détail; vous
          pouvez corriger sa catégorie ou l’exclure de la pseudonymisation.
        </p>
      </div>
      <RelecturePseudonymisation
        {contenuOriginal}
        {contexteOriginal}
        {occurrences}
        {etatRelecture}
        {locuteurs}
        onprojection={(texte, contexteProjete) => {
          contenu = texte;
          contexte = contexteProjete;
        }}
        onlocuteurs={(nouveauxLocuteurs) => {
          locuteurs = nouveauxLocuteurs;
          programmerSauvegarde();
        }}
        onetat={(nouvelEtat) => {
          etatRelecture = nouvelEtat;
          programmerSauvegarde();
        }}
      />
      {#if etatSynchronisation === 'en_attente'}<p role="status" aria-live="polite">
          Enregistrement des modifications…
        </p>
      {:else if etatSynchronisation === 'echec'}<p role="alert">
          La synchronisation a échoué. Gardez cette page ouverte et réessayez.
        </p>
        <button
          class="fr-btn fr-btn--secondary"
          type="button"
          onclick={() => void sauvegarderEtat()}>Réessayer l’enregistrement</button
        >{/if}
      {#if conflitsCategoriesFusionnes}<div
          class="fr-alert fr-alert--warning"
          role="status"
        >
          <p>
            {conflitsCategoriesFusionnes} élément(s) ont reçu une catégorie prudente. Relisez-les
            avant confirmation.
          </p>
        </div>{/if}
      <fieldset class="locuteurs">
        <legend>Rôle des locuteurs</legend>
        {#each locuteurs as locuteur, index (locuteur.identifiant)}
          <div class="locuteur">
            <label class="fr-label" for={`role-${index}`}
              >Locuteur {index + 1} · {locuteur.nom_affiche ||
                locuteur.identifiant}</label
            >
            <select
              class="fr-select"
              id={`role-${index}`}
              bind:value={locuteur.role}
              onchange={programmerSauvegarde}
            >
              <option value="interne">Interne</option><option value="externe"
                >Externe</option
              ><option value="indetermine">Indéterminé</option>
            </select>
            <label class="fr-label" for={`justification-${index}`}
              >Justification du rôle</label
            >
            <input
              class="fr-input"
              id={`justification-${index}`}
              bind:value={locuteur.justification}
              oninput={programmerSauvegarde}
            />
          </div>
        {/each}
      </fieldset>
      <div class="pied-relecture">
        <button
          class="fr-btn fr-btn--secondary"
          type="button"
          onclick={abandonnerPreparation}
          >Abandonner et supprimer le brouillon</button
        >
        <ConfirmationPseudonymisation
          modalId="confirmation-pseudonymiser-pdf"
          confirmationNecessaire={true}
          desactive={enCours ||
            !dateEntretien ||
            etatSynchronisation !== 'enregistre'}
          {enCours}
          {erreur}
          onconfirmer={confirmer}
        />
      </div>
      {#if problemes.length}<ul class="problemes" aria-label="Éléments à corriger">
          {#each problemes as probleme (probleme.categorie + probleme.element)}<li>
              <strong>{probleme.categorie} — {probleme.element} :</strong>
              {probleme.raison}
            </li>{/each}
        </ul>{/if}
    </section>
  {/if}
</main>

<style>
  .contenu {
    display: grid;
    gap: 24px;
    width: 100%;
  }
  .etape {
    display: grid;
    gap: 8px;
  }
  .etape p,
  .etape h2 {
    margin: 0;
  }
  .etape h2 {
    font-size: 24px;
  }
  .barres {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 4px;
    margin-top: 8px;
  }
  .barres span {
    height: 6px;
    background: var(--background-contrast-grey, #eee);
  }
  .barres span.on {
    background: var(--border-action-high-blue-france, #8585f6);
  }
  .suite {
    margin: 0;
    font-size: 12px;
    color: var(--text-mention-grey, #666);
  }
  .import {
    display: grid;
    gap: 24px;
  }
  .champ {
    display: grid;
    gap: 6px;
  }
  .champ label {
    margin: 0;
  }
  .optionnel,
  .champ .fr-hint-text {
    color: var(--text-mention-grey, #666);
    font-size: 14px;
    font-weight: 400;
  }
  .depot {
    min-height: 200px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 10px;
    border: 1px dashed var(--border-default-grey, #929292);
    background: var(--background-alt-grey, #f6f6f6);
    padding: 24px;
    text-align: center;
    cursor: pointer;
    overflow-wrap: anywhere;
  }
  .depot > span:first-child {
    color: var(--text-action-high-blue-france);
    font-size: 32px;
  }
  .depot .fr-btn {
    margin: 0;
  }
  .sr-only {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    white-space: nowrap;
    border: 0;
  }
  .actions-import,
  .pied-relecture {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 16px;
  }
  .actions-import .fr-btn,
  .pied-relecture :global(.fr-btn) {
    margin: 0;
  }
  .actions-import span,
  .relecture-tete > p {
    font-size: 14px;
    color: var(--text-mention-grey, #666);
  }
  .traitement {
    display: grid;
    gap: 12px;
    border: 1px solid var(--border-default-grey);
    padding: 24px;
  }
  .traitement h3,
  .traitement p {
    margin: 0;
  }
  .jauge-ligne {
    display: flex;
    justify-content: space-between;
    gap: 16px;
  }
  .jauge {
    height: 10px;
    overflow: hidden;
    background: var(--background-contrast-grey, #eee);
  }
  .jauge div {
    height: 100%;
    background: var(--border-action-high-blue-france, #8585f6);
    transition: width 200ms ease;
  }
  .jauge .indeterminee {
    width: 35%;
    animation: progression 1.5s ease-in-out infinite alternate;
  }
  .temps {
    font-size: 14px;
    color: var(--text-mention-grey, #666);
  }
  .relecture-page {
    display: grid;
    gap: 24px;
  }
  .relecture-tete {
    display: flex;
    flex-wrap: wrap;
    gap: 20px 40px;
    align-items: flex-end;
  }
  .relecture-tete .champ {
    flex: 0 1 280px;
  }
  .relecture-tete > p {
    flex: 1 1 360px;
    margin: 0;
    line-height: 1.6;
  }
  .locuteurs {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(min(100%, 220px), 1fr));
    gap: 12px;
    border: 1px solid var(--border-default-grey);
    padding: 16px;
  }
  .locuteurs legend {
    font-weight: 700;
  }
  .locuteur {
    display: grid;
    gap: 6px;
  }
  .pied-relecture {
    justify-content: flex-end;
    border-top: 1px solid var(--border-default-grey);
    padding-top: 20px;
  }
  .problemes {
    color: var(--text-default-error, #ce0500);
  }
  .fr-alert {
    margin: 0;
  }
  @keyframes progression {
    to {
      transform: translateX(185%);
    }
  }
  @media (max-width: 600px) {
    .depot {
      min-height: 180px;
    }
    .pied-relecture {
      justify-content: stretch;
    }
    .pied-relecture :global(.fr-btn) {
      width: 100%;
    }
  }
</style>
