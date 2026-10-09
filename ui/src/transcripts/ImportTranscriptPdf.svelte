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
  let locuteurs = $state<
    {
      identifiant: string;
      role: 'interne' | 'externe' | 'indetermine';
      justification: string;
    }[]
  >([]);
  let remplacements = $state<
    {
      valeur_originale: string;
      valeur_anonyme: string;
      categorie: string;
      champ: string;
    }[]
  >([]);
  let problemes = $state<{ categorie: string; element: string; raison: string }[]>(
    []
  );
  let selectionProjet = $state(0);
  let transcriptId = $state<number | null>(null);
  let analyse = $state<unknown>(null);
  let relancerAnalyse = $state(false);
  const contenuAnalyse = $derived(
    typeof analyse === 'object' && analyse !== null && 'contenu' in analyse
      ? (analyse.contenu as Record<string, unknown>)
      : {}
  );
  let erreur = $state('');
  let enCours = $state(false);
  let progression = $state<ProgressionPreparation | null>(null);
  let jetonPreparation = $state<string | null>(null);
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
    selectionProjet = projetId ?? 0;
    if (typeSource === 'produit')
      listerProjets(produitId)
        .then((valeur) => (projets = valeur))
        .finally(() => (projetsCharges = true));
    fetch(`/api/transcripts-pdf/produits/${produitId}`)
      .then((reponse) => reponse.json())
      .then((valeur) => {
        sources = valeur.filter(
          (source: { type_source: string }) => source.type_source === typeSource
        );
      });
    return () => {
      monte = false;
      controleEnvoi?.abort();
      controleSuivi?.abort();
      annulerAttente();
      arreterHorloge();
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
    enCours = true;
    progression = null;
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

  async function preparer() {
    if (!fichier || enCours || jetonPreparation) return;
    enCours = true;
    progression = null;
    arreterHorloge();
    erreur = '';
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
      jeton = demande.jeton;
      jetonPreparation = jeton;
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
          arreterHorloge();
          erreur = resultat.erreur;
          return;
        }
        if (resultat.statut === 'termine') {
          contenu = resultat.contenu;
          contexte = resultat.contexte;
          nomSource = resultat.nom_source;
          dateEntretien = resultat.date_entretien ?? '';
          locuteurs = resultat.locuteurs;
          remplacements = resultat.remplacements;
          jetonPreparation = null;
          arreterHorloge();
          return;
        }
        await attendre(2000);
      }
    } catch (cause) {
      if (!monte) return;
      if (cause instanceof ErreurSuiviPreparation && cause.code === 'introuvable') {
        jetonPreparation = null;
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

  async function confirmer() {
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
      transcriptId = resultat.id;
      edition = false;
      await consulter(resultat.id);
    } catch (cause) {
      erreur = cause instanceof Error ? cause.message : 'Enregistrement impossible.';
    } finally {
      enCours = false;
    }
  }

  async function analyser() {
    if (!transcriptId) return;
    enCours = true;
    progression = null;
    erreur = '';
    try {
      const reponse = await fetch(
        `/api/transcripts-pdf/${transcriptId}/analyse?relancer=${relancerAnalyse}`,
        { method: 'POST' }
      );
      const resultat = await reponse.json();
      if (!reponse.ok) throw new Error(resultat.detail ?? 'Analyse impossible.');
      if (resultat.analyse) analyse = resultat.analyse;
      else {
        analyse = { statut: 'en_cours' };
        for (let tentative = 0; tentative < 90; tentative += 1) {
          await new Promise((resoudre) => setTimeout(resoudre, 2000));
          const suivi = await fetch(`/api/transcripts-pdf/${transcriptId}/job`).then(
            (r) => r.json()
          );
          if (suivi.statut === 'termine') {
            relancerAnalyse = false;
            analyse = await fetch(
              `/api/transcripts-pdf/${transcriptId}/analyse`
            ).then((r) => r.json());
            break;
          }
          if (suivi.statut === 'echec') {
            relancerAnalyse = true;
            throw new Error('L’analyse a échoué. Vous pouvez la relancer.');
          }
        }
      }
    } catch (cause) {
      erreur = cause instanceof Error ? cause.message : 'Analyse impossible.';
    } finally {
      enCours = false;
    }
  }
</script>

<main class="contenu">
  <h1>
    Importer un transcript PDF {typeSource === 'produit' ? 'produit' : 'BizDev'}
  </h1>
  {#if sources.length}
    <h2>Transcripts enregistrés</h2>
    <table>
      <thead
        ><tr><th>Nom de source</th><th>Date</th><th>Projet</th><th></th></tr></thead
      >
      <tbody
        >{#each sources as source (source.id)}
          <tr
            ><td>{source.nom_source}</td><td
              >{source.date_entretien ?? 'À compléter'}</td
            ><td
              >{projets.find((projet) => projet.id === source.projet_id)?.nom ??
                '—'}</td
            ><td
              ><button
                class="fr-btn fr-btn--secondary"
                onclick={() => consulter(source.id)}>Consulter</button
              ></td
            ></tr
          >
        {/each}</tbody
      >
    </table>
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
          onchange={(event) => (fichier = event.currentTarget.files?.[0] ?? null)}
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
        >{enCours ? 'Préparation…' : 'Préparer et anonymiser'}</button
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
      <label for="date">Date de l’entretien</label>
      <input id="date" type="date" bind:value={dateEntretien} required />
      {#if typeSource === 'produit'}
        <label for="projet">Projet de recherche</label>
        <select id="projet" bind:value={selectionProjet} required>
          <option value={0}>Choisir un projet</option>
          {#each projets as projet (projet.id)}<option value={projet.id}
              >{projet.nom}</option
            >{/each}
        </select>
      {/if}
      <label class="fr-label" for="transcript">Transcript anonymisé</label>
      <textarea class="fr-input" id="transcript" bind:value={contenu} rows="14"
      ></textarea>
      {#if remplacements.length}
        <h2>Remplacements proposés</h2>
        <table>
          <thead
            ><tr
              ><th>Champ</th><th>Valeur détectée</th><th>Remplacement</th><th
                >Catégorie</th
              ></tr
            ></thead
          >
          <tbody
            >{#each remplacements as remplacement (remplacement.champ + remplacement.valeur_originale)}
              <tr
                ><td
                  >{remplacement.champ === 'transcript'
                    ? 'Transcript'
                    : 'Contexte'}</td
                ><td>{remplacement.valeur_originale}</td><td
                  >{remplacement.valeur_anonyme}</td
                ><td>{remplacement.categorie}</td></tr
              >
            {/each}</tbody
          >
        </table>
      {/if}
      <div class="fr-input-group">
        <label class="fr-label" for="contexte-edite">Contexte anonymisé</label>
        <textarea class="fr-input" id="contexte-edite" bind:value={contexte} rows="4"
        ></textarea>
      </div>
      <fieldset>
        <legend>Rôle des locuteurs</legend>
        {#each locuteurs as locuteur, index (locuteur.identifiant)}
          <label for={`role-${index}`}>{locuteur.identifiant}</label>
          <select id={`role-${index}`} bind:value={locuteur.role}>
            <option value="interne">ANSSI / laboratoire</option><option
              value="externe">Externe</option
            ><option value="indetermine">Indéterminé</option>
          </select>
          <label for={`justification-${index}`}>Justification</label><input
            id={`justification-${index}`}
            bind:value={locuteur.justification}
          />
        {/each}
      </fieldset>
      <button
        class="fr-btn"
        disabled={enCours ||
          !dateEntretien ||
          (typeSource === 'produit' && !selectionProjet)}
        onclick={confirmer}>Valider et enregistrer</button
      >
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
    <h3>Transcript anonymisé</h3>
    <pre>{contenu}</pre>
    {#if contexte}<h3>Contexte</h3>
      <p>{contexte}</p>{/if}
    <ul>
      {#each locuteurs as locuteur (locuteur.identifiant)}<li>
          {locuteur.identifiant} — {locuteur.role} : {locuteur.justification}
        </li>{/each}
    </ul>
    <button class="fr-btn fr-btn--secondary" onclick={() => (edition = true)}
      >Modifier</button
    >
    <button class="fr-btn" disabled={enCours} onclick={analyser}
      >Lancer l’analyse</button
    >
    {#if analyse}
      <section aria-live="polite">
        <h2>Résumé</h2>
        <p>{String(contenuAnalyse.resume ?? '')}</p>
        {#if Array.isArray(contenuAnalyse.themes)}<h2>Thèmes</h2>
          <ul>
            {#each contenuAnalyse.themes as theme (theme)}<li>{theme}</li>{/each}
          </ul>{/if}
        {#each Object.entries(contenuAnalyse) as [cle, elements] (cle)}
          {#if Array.isArray(elements) && cle !== 'themes'}
            <h2>
              {cle === 'fonctionnalites'
                ? 'Fonctionnalités évoquées'
                : cle.replaceAll('_', ' ')}
            </h2>
            <ul class="extractions">
              {#each elements as element, index (`${cle}-${index}`)}
                <li>
                  {#if typeof element === 'object' && element !== null}
                    {#if 'type' in element}<p>Type : {String(element.type)}</p>{/if}
                    <p>
                      {String(
                        'description' in element
                          ? element.description
                          : 'action' in element
                            ? element.action
                            : ''
                      )}
                    </p>
                    {#if 'verbatim' in element}<blockquote>
                        « {String(element.verbatim)} »
                        <footer>
                          {String(
                            'speaker_id' in element ? element.speaker_id : ''
                          )}, tour {String(
                            'tour_id' in element ? element.tour_id : ''
                          )}
                        </footer>
                      </blockquote>{/if}
                    {#if 'sentiment' in element}<p>
                        Sentiment : {String(
                          element.sentiment
                        )}{#if 'gravite' in element && element.gravite}
                          · Gravité : {String(element.gravite)}{/if}
                      </p>{/if}
                  {/if}
                </li>
              {/each}
            </ul>
          {/if}
        {/each}
      </section>
    {/if}
  {/if}
</main>

<style>
  .contenu {
    box-sizing: border-box;
    margin: 2rem auto;
    max-width: 1000px;
    padding: 0 1rem;
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
  blockquote {
    border-left: 3px solid var(--border-action-high-blue-france);
    margin: 0.75rem 0;
    padding-left: 1rem;
  }
  blockquote footer {
    font-size: 0.875rem;
  }
</style>
