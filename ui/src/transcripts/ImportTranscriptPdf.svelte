<script lang="ts">
  import { onMount } from 'svelte';
  import { creerProjet, listerProjets, type Projet } from '../api/projets';
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
  import NotificationAnalyseTranscript from './NotificationAnalyseTranscript.svelte';
  import { notificationApresAnalyse } from './notification-analyse';
  import RemplacementsTranscript from './RemplacementsTranscript.svelte';
  import RelecturePseudonymisation from './RelecturePseudonymisation.svelte';
  import type { EtatRelecture, OccurrenceSource } from './modele-relecture';
  import PanneauAnalyseTranscript from './PanneauAnalyseTranscript.svelte';
  import { supprimerTranscriptPdf } from '../api/transcripts_pdf';
  import SuppressionConfirmee from '../composants/SuppressionConfirmee.svelte';
  import { decouperLocuteurs } from './modele-locuteurs';
  import TranscriptPseudonymise from './TranscriptPseudonymise.svelte';
  import ConfirmationPseudonymisation from './ConfirmationPseudonymisation.svelte';

  let {
    produitId,
    projetId,
    typeSource,
  }: { produitId: number; projetId?: number; typeSource: 'produit' | 'bizdev' } =
    $props();
  let projets = $state<Projet[]>([]);
  let projetsCharges = $state(false);
  let nomProjet = $state('');
  let briefProjet = $state('');
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
  const contenuAvecLocuteurs = $derived(
    decouperLocuteurs(contenu, locuteurs)
      .map((segment) =>
        segment.type === 'locuteur' ? segment.texte + ':' : segment.texte
      )
      .join('')
  );
  let remplacements = $state<
    {
      valeur_originale: string;
      valeur_anonyme: string;
      categorie: string;
      champ: string;
    }[]
  >([]);
  let conflitsCategoriesFusionnes = $state(0);
  let problemes = $state<{ categorie: string; element: string; raison: string }[]>(
    []
  );
  let selectionProjet = $state(0);
  let transcriptId = $state<number | null>(null);
  let analyse = $state<unknown>(null);
  let analyseEnCours = $state(false);
  let analyseErreur = $state('');
  let notificationAnalyse = $state<'prete' | 'echec' | ''>('');
  let ongletActif = $state<'analyse' | 'transcript'>('analyse');
  let relancerAnalyse = $state(false);
  const contenuAnalyse = $derived(
    typeof analyse === 'object' && analyse !== null && 'contenu' in analyse
      ? (analyse.contenu as Record<string, unknown>)
      : null
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
  let sources = $state<
    {
      id: number;
      type_source: string;
      nom_source: string;
      date_entretien: string | null;
      projet_id: number | null;
    }[]
  >([]);
  let edition = $state(false);
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

  function selectionnerOnglet(onglet: 'analyse' | 'transcript') {
    ongletActif = onglet;
    if (onglet === 'analyse') notificationAnalyse = '';
  }

  function naviguerOnglets(event: KeyboardEvent, onglet: 'analyse' | 'transcript') {
    if (event.key !== 'ArrowRight' && event.key !== 'ArrowLeft') return;
    const suivant = onglet === 'analyse' ? 'transcript' : 'analyse';
    selectionnerOnglet(suivant);
    document.getElementById(`onglet-${suivant}`)?.focus();
  }

  async function chargerSources() {
    const valeur = await fetch(`/api/transcripts-pdf/produits/${produitId}`).then(
      (reponse) => reponse.json()
    );
    sources = valeur.filter(
      (source: { type_source: string }) => source.type_source === typeSource
    );
  }

  onMount(() => {
    monte = true;
    window.addEventListener('beforeunload', avertirAvantSortie);
    selectionProjet = projetId ?? 0;
    if (typeSource === 'produit')
      listerProjets(produitId)
        .then((valeur) => (projets = valeur))
        .finally(() => (projetsCharges = true));
    void chargerSources();
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

  async function creerProjetRecherche() {
    if (!nomProjet.trim() || !briefProjet.trim()) {
      erreur = 'Renseignez le nom et le brief de recherche.';
      return;
    }
    enCours = true;
    erreur = '';
    try {
      const projet = await creerProjet({
        produit_id: produitId,
        nom: nomProjet,
        brief: briefProjet,
      });
      projets = [...projets, projet];
      selectionProjet = projet.id;
      nomProjet = '';
      briefProjet = '';
    } catch (cause) {
      erreur =
        cause instanceof Error ? cause.message : 'Création du projet impossible.';
    } finally {
      enCours = false;
    }
  }

  async function consulter(id: number) {
    contenuOriginal = '';
    contexteOriginal = '';
    occurrences = [];
    remplacements = [];
    enCours = true;
    conflitsCategoriesFusionnes = 0;
    progression = null;
    analyseEnCours = false;
    analyseErreur = '';
    notificationAnalyse = '';
    ongletActif = 'analyse';
    try {
      const source = await fetch(`/api/transcripts-pdf/${id}`).then((reponse) =>
        reponse.json()
      );
      transcriptId = source.id;
      nomSource = source.nom_source;
      dateEntretien = source.date_entretien ?? '';
      contenu = source.contenu;
      contexte = source.contexte;
      locuteurs = source.locuteurs;
      selectionProjet = source.projet_id ?? 0;
      analyse = await fetch(`/api/transcripts-pdf/${id}/analyse`).then((reponse) =>
        reponse.json()
      );
      const job = await fetch(`/api/transcripts-pdf/${id}/job`).then((reponse) =>
        reponse.ok ? reponse.json() : null
      );
      relancerAnalyse = job?.statut === 'echec';
      edition = false;
      erreur = '';
    } catch (cause) {
      erreur = cause instanceof Error ? cause.message : 'Lecture impossible.';
    } finally {
      enCours = false;
    }
  }

  function apresSuppression(id: number) {
    sources = sources.filter((source) => source.id !== id);
    if (transcriptId === id) {
      transcriptId = null;
      analyse = null;
      contenu = '';
      contexte = '';
      nomSource = '';
      dateEntretien = '';
      locuteurs = [];
      edition = false;
    }
  }

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
          etatRelecture = resultat.etat_relecture;
          if (resultat.projet_id !== undefined)
            selectionProjet = resultat.projet_id ?? 0;
          remplacements = resultat.remplacements;
          conflitsCategoriesFusionnes = resultat.conflits_categories_fusionnes;
          etatSynchronisation = 'enregistre';
          versionEnregistree = versionEtat;
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
            projet_id: typeSource === 'produit' ? selectionProjet || null : null,
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
    remplacements = [];
    versionEtat += 1;
    versionEnregistree = versionEtat;
    etatSynchronisation = 'enregistre';
  }

  async function confirmer(): Promise<boolean> {
    enCours = true;
    progression = null;
    erreur = '';
    try {
      const reponse = await fetch(
        transcriptId
          ? `/api/transcripts-pdf/${transcriptId}`
          : '/api/transcripts-pdf',
        {
          method: transcriptId ? 'PUT' : 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            type_source: typeSource,
            nom_source: nomSource,
            produit_id: produitId,
            projet_id: typeSource === 'produit' ? selectionProjet : null,
            date_entretien: dateEntretien || null,
            contenu,
            contexte,
            locuteurs,
          }),
        }
      );
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
      await chargerSources();
      await abandonnerPreparation();
      contenuOriginal = '';
      contexteOriginal = '';
      occurrences = [];
      transcriptId = resultat.id;
      edition = false;
      await consulter(resultat.id);
      return true;
    } catch (cause) {
      erreur = cause instanceof Error ? cause.message : 'Enregistrement impossible.';
      return false;
    } finally {
      enCours = false;
    }
  }

  async function analyser() {
    if (!transcriptId || enCours) return;
    enCours = true;
    analyseEnCours = true;
    progression = null;
    erreur = '';
    analyseErreur = '';
    notificationAnalyse = '';
    try {
      const reponse = await fetch(
        `/api/transcripts-pdf/${transcriptId}/analyse?relancer=${relancerAnalyse}`,
        { method: 'POST' }
      );
      const resultat = await reponse.json();
      if (!reponse.ok) throw new Error(resultat.detail ?? 'Analyse impossible.');
      let terminee = Boolean(resultat.analyse);
      if (resultat.analyse) {
        analyse = resultat.analyse;
      } else {
        for (let tentative = 0; tentative < 90; tentative += 1) {
          await new Promise((resoudre) => setTimeout(resoudre, 2000));
          const suivi = await fetch(`/api/transcripts-pdf/${transcriptId}/job`).then(
            (r) => r.json()
          );
          if (suivi.statut === 'termine') {
            const resultatAnalyse = await fetch(
              `/api/transcripts-pdf/${transcriptId}/analyse`
            ).then((r) => r.json());
            if (!resultatAnalyse)
              throw new Error(
                'L’analyse est terminée, mais son résultat est introuvable.'
              );
            analyse = resultatAnalyse;
            terminee = true;
            break;
          }
          if (suivi.statut === 'echec') {
            relancerAnalyse = true;
            throw new Error('L’analyse a échoué. Vous pouvez la relancer.');
          }
        }
      }
      if (!terminee)
        throw new Error(
          'Le suivi de l’analyse a dépassé le délai. Vous pouvez le reprendre.'
        );
      relancerAnalyse = false;
      notificationAnalyse = notificationApresAnalyse(ongletActif, 'prete');
    } catch (cause) {
      analyseErreur = cause instanceof Error ? cause.message : 'Analyse impossible.';
      notificationAnalyse = notificationApresAnalyse(ongletActif, 'echec');
    } finally {
      enCours = false;
      analyseEnCours = false;
    }
  }
</script>

<main class="contenu">
  <h1>
    Importer un transcript PDF {typeSource === 'produit' ? 'produit' : 'BizDev'}
  </h1>
  {#if sources.length}
    <h2>Transcripts enregistrés</h2>
    <div class="tableau">
      <table>
        <thead
          ><tr><th>Nom de source</th><th>Date</th><th>Projet</th><th>Actions</th></tr
          ></thead
        ><tbody
          >{#each sources as source (source.id)}
            <tr
              ><td>{source.nom_source}</td><td
                >{source.date_entretien ?? 'À compléter'}</td
              ><td
                >{projets.find((projet) => projet.id === source.projet_id)?.nom ??
                  '—'}</td
              ><td
                ><div class="actions-source">
                  <button
                    class="fr-btn fr-btn--secondary"
                    type="button"
                    onclick={() => consulter(source.id)}>Consulter</button
                  >
                  <a
                    class="fr-btn fr-btn--secondary"
                    href={`/api/transcripts-pdf/${source.id}/pdf`}
                    aria-label={`Télécharger le transcript pseudonymisé de ${source.nom_source} en PDF`}
                    download>Télécharger PDF</a
                  >
                  <SuppressionConfirmee
                    modalId={`suppression-transcript-${source.id}`}
                    titre={`Supprimer le transcript « ${source.nom_source} » ?`}
                    description="Le transcript PDF, son analyse générée et ses données dérivées seront supprimés définitivement."
                    onconfirmer={() => supprimerTranscriptPdf(source.id)}
                    onsucces={() => apresSuppression(source.id)}
                  />
                </div></td
              ></tr
            >
          {/each}</tbody
        >
      </table>
    </div>
  {/if}
  {#if erreur}<p class="erreur" role="alert">{erreur}</p>{/if}
  {#if !transcriptId || edition}
    {#if !contenu && !transcriptId}
      {#if typeSource === 'produit'}
        {#if !projetsCharges}
          <p>Chargement des projets…</p>
        {:else if projets.length}
          <label class="fr-label" for="projet-import">Projet de recherche</label>
          <select
            class="fr-select"
            id="projet-import"
            bind:value={selectionProjet}
            required
          >
            <option value={0}>Choisir un projet</option>
            {#each projets as projet (projet.id)}
              <option value={projet.id}>{projet.nom}</option>
            {/each}
          </select>
        {:else}
          <fieldset>
            <legend>Créer un projet de recherche</legend>
            <label class="fr-label" for="nom-projet-import">Nom du projet</label>
            <input
              class="fr-input"
              id="nom-projet-import"
              bind:value={nomProjet}
              required
            />
            <label class="fr-label" for="brief-projet-import"
              >Brief de recherche</label
            >
            <textarea
              class="fr-input"
              id="brief-projet-import"
              bind:value={briefProjet}
              required
            ></textarea>
            <button
              class="fr-btn fr-btn--secondary"
              disabled={enCours}
              onclick={creerProjetRecherche}
            >
              {enCours ? 'Création…' : 'Créer le projet'}
            </button>
          </fieldset>
        {/if}
      {/if}
      <div class="fr-upload-group">
        <label class="fr-label" for="pdf">
          Fichier PDF
          <span class="fr-hint-text" id="pdf-aide">Format PDF, 10 Mo maximum</span>
        </label>
        <input
          class="fr-upload"
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
            remplacements = [];
            fichier = event.currentTarget.files?.[0] ?? null;
          }}
        />
      </div>
      <div class="fr-input-group">
        <label class="fr-label" for="contexte"
          >Contexte complémentaire (facultatif)</label
        >
        <textarea class="fr-input" id="contexte" bind:value={contexte} rows="4"
        ></textarea>
      </div>
      <button
        class="fr-btn"
        disabled={!fichier ||
          enCours ||
          jetonPreparation !== null ||
          (typeSource === 'produit' && (!projetsCharges || !selectionProjet))}
        onclick={preparer}
        >{enCours ? 'Préparation…' : 'Préparer et pseudonymiser'}</button
      >
      {#if jetonPreparation && !enCours}
        <button
          class="fr-btn fr-btn--secondary"
          type="button"
          onclick={() => suivrePreparation()}>Reprendre le suivi</button
        >
      {/if}
      {#if progression && (enCours || jetonPreparation)}
        {@const pourcentage = pourcentageProgression(progression)}
        <div class="progression">
          <div
            role="progressbar"
            aria-label="Progression de la préparation du transcript"
            aria-valuemin="0"
            aria-valuemax="100"
            aria-valuenow={pourcentage ?? undefined}
            aria-valuetext={pourcentage === null
              ? libelleProgression(progression)
              : `${progression.groupes_termines} groupes analysés sur ${progression.groupes_total}`}
          >
            {#if pourcentage !== null}
              <div
                class="progression__valeur"
                style={`width: ${pourcentage}%`}
              ></div>
            {:else}
              <div class="progression__indeterminee"></div>
            {/if}
          </div>
          <p aria-live="polite">{libelleProgression(progression)}</p>
          {#if progression.phase === 'anonymisation' && progression.groupes_total !== null}
            <p>
              Groupes analysés : {progression.groupes_termines} sur {progression.groupes_total}
            </p>
            {#if progression.groupes_en_cours.length > 0}
              <p>Groupes en cours : {progression.groupes_en_cours.join(', ')}</p>
            {/if}
          {/if}
          <p>
            Temps écoulé depuis l’envoi : {dureeDepuisSoumission(
              progression.duree_secondes
            )}
          </p>
        </div>
      {/if}
    {:else}
      <div class="fr-input-group" class:fr-input-group--error={!dateEntretien}>
        <label class="fr-label" for="date">Date de l’entretien</label>
        <input
          class="fr-input"
          id="date"
          type="date"
          bind:value={dateEntretien}
          aria-invalid={!dateEntretien}
          aria-describedby={!dateEntretien ? 'date-messages' : undefined}
          onchange={programmerSauvegarde}
          required
        />
        {#if !dateEntretien}
          <div class="fr-messages-group" id="date-messages" aria-live="polite">
            <p class="fr-message fr-message--error">
              La date de l’entretien est obligatoire. Renseignez-la pour activer
              “Valider et enregistrer”.
            </p>
          </div>
        {/if}
      </div>
      {#if typeSource === 'produit'}
        <div class="fr-select-group" class:fr-select-group--error={!selectionProjet}>
          <label class="fr-label" for="projet">Projet de recherche</label>
          <select
            class="fr-select"
            id="projet"
            bind:value={selectionProjet}
            aria-invalid={!selectionProjet}
            aria-describedby={!selectionProjet ? 'projet-messages' : undefined}
            required
            onchange={programmerSauvegarde}
          >
            <option value={0}>Choisir un projet</option>
            {#each projets as projet (projet.id)}
              <option value={projet.id}>{projet.nom}</option>
            {/each}
          </select>
          {#if !selectionProjet}
            <div class="fr-messages-group" id="projet-messages" aria-live="polite">
              <p class="fr-message fr-message--error">
                Choisissez un projet pour activer “Valider et enregistrer”.
              </p>
            </div>
          {/if}
        </div>
      {/if}
      {#if contenuOriginal}
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
        {#if etatSynchronisation === 'en_attente'}
          <p role="status" aria-live="polite">Enregistrement des modifications…</p>
        {:else if etatSynchronisation === 'echec'}
          <p role="alert">
            La synchronisation a échoué. Gardez cette page ouverte et réessayez.
          </p>
        {/if}
        <button
          class="fr-btn fr-btn--secondary"
          type="button"
          onclick={abandonnerPreparation}
          >Abandonner et supprimer le brouillon</button
        >
        {#if conflitsCategoriesFusionnes}
          <div class="fr-alert fr-alert--warning" role="status">
            <p>
              {conflitsCategoriesFusionnes} identité(s) ou zone(s) de chevauchement ont
              reçu une catégorie prudente. Relisez les masques avant confirmation.
            </p>
          </div>
        {/if}
      {:else}
        <TranscriptPseudonymise
          bind:contenu
          mode="edition"
          id="transcript"
          lignes={14}
        />
        <RemplacementsTranscript {remplacements} {conflitsCategoriesFusionnes} />
        <div class="fr-input-group">
          <TranscriptPseudonymise
            bind:contenu={contexte}
            mode="edition"
            id="contexte-edite"
            titre="Contexte pseudonymisé"
            lignes={4}
            legende={false}
          />
        </div>
      {/if}
      <fieldset>
        <legend>Rôle des locuteurs</legend>
        <p>
          Interne · {locuteurs.filter((locuteur) => locuteur.role === 'interne')
            .length} / Externe · {locuteurs.filter(
            (locuteur) => locuteur.role === 'externe'
          ).length} / Indéterminé · {locuteurs.filter(
            (locuteur) => locuteur.role === 'indetermine'
          ).length}
        </p>
        {#each locuteurs as locuteur, index (locuteur.identifiant)}
          <label for={`role-${index}`}
            >Participant {index + 1} · {locuteur.nom_affiche ||
              locuteur.identifiant}</label
          >
          <select
            id={`role-${index}`}
            bind:value={locuteur.role}
            onchange={programmerSauvegarde}
          >
            <option value="interne">Interne · {index + 1}</option><option
              value="externe">Externe · {index + 1}</option
            ><option value="indetermine">Indéterminé · {index + 1}</option>
          </select>
          <label for={`justification-${index}`}>Justification</label><input
            id={`justification-${index}`}
            bind:value={locuteur.justification}
          />
        {/each}
      </fieldset>
      <ConfirmationPseudonymisation
        modalId="confirmation-pseudonymisation"
        confirmationNecessaire={!transcriptId}
        desactive={enCours ||
          !dateEntretien ||
          (typeSource === 'produit' && !selectionProjet)}
        {enCours}
        {erreur}
        onconfirmer={confirmer}
      />
      {#if problemes.length}
        <ul class="problemes" aria-label="Éléments à corriger">
          {#each problemes as probleme (probleme.categorie + probleme.element)}
            <li>
              <strong>{probleme.categorie} — {probleme.element} :</strong>
              {probleme.raison}
            </li>
          {/each}
        </ul>
      {/if}
    {/if}
  {:else}
    <h2>{nomSource}</h2>
    <p>Date : {dateEntretien}</p>
    <div class="onglets" role="tablist" aria-label="Contenu du transcript">
      <button
        id="onglet-analyse"
        class:actif={ongletActif === 'analyse'}
        role="tab"
        aria-selected={ongletActif === 'analyse'}
        aria-controls="panneau-analyse"
        tabindex={ongletActif === 'analyse' ? 0 : -1}
        onclick={() => selectionnerOnglet('analyse')}
        onkeydown={(event) => naviguerOnglets(event, 'analyse')}
        >Analyse générée{#if notificationAnalyse}<span class="indicateur-onglet"
            >{notificationAnalyse === 'prete' ? 'Résultat prêt' : 'Erreur'}</span
          >{/if}</button
      >
      <button
        id="onglet-transcript"
        class:actif={ongletActif === 'transcript'}
        role="tab"
        aria-selected={ongletActif === 'transcript'}
        aria-controls="panneau-transcript"
        tabindex={ongletActif === 'transcript' ? 0 : -1}
        onclick={() => selectionnerOnglet('transcript')}
        onkeydown={(event) => naviguerOnglets(event, 'transcript')}
        >Transcript pseudonymisé</button
      >
    </div>
    {#if notificationAnalyse}
      <NotificationAnalyseTranscript
        statut={notificationAnalyse}
        voirAnalyse={() => selectionnerOnglet('analyse')}
      />
    {/if}
    <div
      id="panneau-analyse"
      role="tabpanel"
      aria-labelledby="onglet-analyse"
      hidden={ongletActif !== 'analyse'}
    >
      <PanneauAnalyseTranscript
        contenu={contenuAnalyse}
        chargement={analyseEnCours}
        desactive={enCours}
        erreur={analyseErreur}
        relancer={relancerAnalyse}
        lancer={analyser}
      />
    </div>
    <div
      id="panneau-transcript"
      role="tabpanel"
      aria-labelledby="onglet-transcript"
      hidden={ongletActif !== 'transcript'}
    >
      <TranscriptPseudonymise contenu={contenuAvecLocuteurs} />
      {#if contexte}<h3>Contexte</h3>
        <p>{contexte}</p>{/if}
      <ul>
        {#each locuteurs as locuteur (locuteur.identifiant)}<li>
            {locuteur.nom_affiche || locuteur.identifiant} — {locuteur.role} :
            {locuteur.justification}
          </li>{/each}
      </ul>
      <div class="actions-transcript">
        <button
          class="fr-btn fr-btn--secondary"
          type="button"
          onclick={() => (edition = true)}>Modifier</button
        >
        <a
          class="fr-btn fr-btn--secondary"
          href={`/api/transcripts-pdf/${transcriptId}/pdf`}
          download>Télécharger PDF</a
        >
      </div>
    </div>
  {/if}
</main>

<style>
  .contenu {
    box-sizing: border-box;
    margin: 2rem auto;
    max-width: 1000px;
    padding: 0 1rem;
  }
  .actions-source {
    align-items: center;
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
  }
  .actions-source :global(.fr-btn) {
    margin: 0;
  }
  .tableau {
    max-width: 100%;
    overflow-x: auto;
  }
  table {
    border-collapse: collapse;
    min-width: 48rem;
    width: 100%;
  }
  th,
  td {
    padding: 1rem;
    text-align: left;
    vertical-align: middle;
  }
  .actions-transcript {
    align-items: center;
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
  }
  .actions-transcript button {
    margin: 0;
  }
  label {
    display: block;
    font-weight: 600;
    margin: 1.25rem 0 0.4rem;
  }
  input:not([type='file']),
  select,
  textarea {
    box-sizing: border-box;
    display: block;
    max-width: 100%;
    padding: 0.6rem;
    width: 100%;
  }
  #transcript {
    font-family: monospace;
  }
  button {
    margin-top: 1.5rem;
  }
  .onglets {
    border-bottom: 1px solid var(--border-default-grey);
    display: flex;
    gap: 1.5rem;
    margin-top: 2rem;
    overflow-x: auto;
  }
  .onglets button {
    background: transparent;
    border: 0;
    border-bottom: 0.25rem solid transparent;
    color: var(--text-action-high-blue-france);
    cursor: pointer;
    flex: 0 0 auto;
    font: inherit;
    padding: 0.75rem 0;
    white-space: nowrap;
  }
  .onglets button.actif {
    border-color: var(--border-action-high-blue-france);
    font-weight: 700;
  }
  .indicateur-onglet {
    background: var(--background-contrast-info);
    border-radius: 0.25rem;
    color: var(--text-default-info);
    font-size: 0.875rem;
    margin-left: 0.5rem;
    padding: 0.125rem 0.375rem;
  }
  [role='tabpanel'] {
    margin-top: 1.5rem;
  }
  fieldset {
    margin-top: 1.5rem;
  }
  .erreur {
    color: #b34000;
  }
  .progression {
    margin-top: 1rem;
  }
  [role='progressbar'] {
    background: var(--background-contrast-grey);
    height: 0.5rem;
    overflow: hidden;
  }
  .progression__valeur,
  .progression__indeterminee {
    background: var(--border-action-high-blue-france);
    height: 100%;
    transition: width 200ms ease;
  }
  .progression__indeterminee {
    animation: progression 1.5s ease-in-out infinite alternate;
    width: 35%;
  }
  @keyframes progression {
    to {
      transform: translateX(185%);
    }
  }
</style>
