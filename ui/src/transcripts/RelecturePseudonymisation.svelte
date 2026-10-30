<script lang="ts">
  import { onMount, tick } from 'svelte';
  import {
    categoriesRelecture,
    ModeleRelecture,
    type CategorieRelecture,
    type EtatRelecture,
    type OccurrenceSource,
  } from './modele-relecture';
  import {
    decouperLocuteurs,
    type LocuteurRelecture,
    type SegmentLocuteur,
  } from './modele-locuteurs';

  type Morceau = SegmentLocuteur | { type: 'masque'; identifiant: string };

  let {
    contenuOriginal,
    contexteOriginal,
    occurrences,
    etatRelecture,
    locuteurs,
    onprojection,
    onlocuteurs,
    onetat,
  }: {
    contenuOriginal: string;
    contexteOriginal: string;
    occurrences: OccurrenceSource[];
    etatRelecture?: EtatRelecture;
    locuteurs: LocuteurRelecture[];
    onprojection: (contenu: string, contexte: string) => void;
    onlocuteurs: (locuteurs: LocuteurRelecture[]) => void;
    onetat: (etat: EtatRelecture) => void;
  } = $props();
  const modele = $derived(
    new ModeleRelecture(
      contenuOriginal,
      contexteOriginal,
      occurrences,
      etatRelecture
    )
  );
  let valeurSelectionnee = $state<string | null>(null);
  let valeurRevelee = $state<string | null>(null);
  let conteneur: HTMLElement;
  let revision = $state(0);
  let texteSelectionne = $state('');
  let categorieSelection = $state<CategorieRelecture>('donnee_sensible');
  let refusSelection = $state(false);
  let messageMasqueObligatoire = $state('');
  let positionPopup = $state<{ gauche: number; haut: number } | null>(null);
  let popupSelection = $state<HTMLElement>();
  let plageSelectionnee: Range | null = null;
  let minuteurSelection: ReturnType<typeof setTimeout> | null = null;
  let framePositionPopup: number | null = null;
  let segmentLocuteurEnEdition = $state<string | null>(null);
  let nomLocuteurSaisi = $state('');
  let champNomLocuteur = $state<HTMLInputElement | undefined>();
  let zoneDefilante: HTMLElement;
  const masques = $derived.by(() => {
    void revision;
    return modele.lireMasques();
  });
  const masqueSelectionne = $derived(
    masques.find((m) => m.identifiant === valeurSelectionnee)
  );
  const indexSelection = $derived(
    masques.findIndex((m) => m.identifiant === valeurSelectionnee)
  );
  const compteSelection = $derived.by(() => {
    void revision;
    return modele
      .lireOccurrences()
      .filter((o) => o.masque_identifiant === valeurSelectionnee).length;
  });
  const segments = $derived.by(() => {
    void revision;
    return construireSegments();
  });

  function construireSegments() {
    return (['transcript', 'contexte'] as const).map((champ) => {
      const source = champ === 'transcript' ? contenuOriginal : contexteOriginal;
      const plages = modele
        .lireOccurrences()
        .filter((o) => o.champ === champ)
        .sort((a, b) => a.debut - b.debut);
      let debut = 0;
      const morceaux: Morceau[] = [];
      for (const plage of plages) {
        morceaux.push(...morceauxTexte(source.slice(debut, plage.debut), champ));
        morceaux.push({ type: 'masque', identifiant: plage.masque_identifiant });
        debut = plage.fin;
      }
      morceaux.push(...morceauxTexte(source.slice(debut), champ));
      return { champ, morceaux };
    });
  }

  function morceauxTexte(texte: string, champ: 'transcript' | 'contexte') {
    if (!texte) return [];
    return champ === 'transcript'
      ? decouperLocuteurs(texte, locuteurs)
      : [{ type: 'texte' as const, texte }];
  }

  function rafraichir() {
    revision += 1;
    onprojection(modele.projeter('transcript'), modele.projeter('contexte'));
    onetat(modele.lireEtat());
  }

  function annuler() {
    if (!modele.annuler()) return;
    if (!modele.lireMasques().some((m) => m.identifiant === valeurSelectionnee))
      valeurSelectionnee = modele.lireMasques()[0]?.identifiant ?? null;
    rafraichir();
  }

  function retablir() {
    if (!modele.retablir()) return;
    if (!modele.lireMasques().some((m) => m.identifiant === valeurSelectionnee))
      valeurSelectionnee = modele.lireMasques()[0]?.identifiant ?? null;
    rafraichir();
  }

  function basculer(valeur: string) {
    valeurSelectionnee = valeur;
    if (!modele.basculer(valeur)) {
      messageMasqueObligatoire = 'Masque obligatoire — liste noire';
      return;
    }
    messageMasqueObligatoire = '';
    valeurRevelee = null;
    rafraichir();
  }

  function categoriser(event: Event) {
    if (!valeurSelectionnee) return;
    modele.categoriser(
      valeurSelectionnee,
      (event.currentTarget as HTMLSelectElement).value as CategorieRelecture
    );
    rafraichir();
  }

  function ajouterSelection() {
    const valeur = texteSelectionne;
    if (!valeur) return;
    refusSelection = !modele.ajouterValeur(valeur, categorieSelection);
    if (refusSelection) return;
    valeurSelectionnee = modele.selection;
    fermerAjoutSelection();
    window.getSelection()?.removeAllRanges();
    rafraichir();
  }

  function fermerAjoutSelection() {
    texteSelectionne = '';
    refusSelection = false;
    plageSelectionnee = null;
    positionPopup = null;
  }

  async function positionnerPopup() {
    await tick();
    if (!texteSelectionne || !plageSelectionnee || !popupSelection) return;
    const selection = plageSelectionnee.getBoundingClientRect();
    const popup = popupSelection.getBoundingClientRect();
    const gauche = Math.min(
      Math.max(8, selection.left + (selection.width - popup.width) / 2),
      window.innerWidth - popup.width - 8
    );
    const haut = Math.max(
      8,
      selection.top - popup.height - 10 >= 8
        ? selection.top - popup.height - 10
        : selection.bottom + 10
    );
    positionPopup = {
      gauche,
      haut: Math.min(haut, window.innerHeight - popup.height - 8),
    };
  }

  function programmerPositionPopup() {
    if (framePositionPopup !== null) return;
    framePositionPopup = requestAnimationFrame(() => {
      framePositionPopup = null;
      void positionnerPopup();
    });
  }

  function parcourir(sens: -1 | 1) {
    if (!masques.length) return;
    valeurSelectionnee =
      masques[(indexSelection + sens + masques.length) % masques.length].identifiant;
    modele.selectionner(valeurSelectionnee);
    valeurRevelee = null;
    revision += 1;
    onetat(modele.lireEtat());
    const cible = zoneDefilante.querySelector<HTMLButtonElement>(
      '[data-masque="' + CSS.escape(valeurSelectionnee ?? '') + '"]'
    );
    if (!cible) return;
    cible.focus({ preventScroll: true });
    const zone = zoneDefilante.getBoundingClientRect();
    const occurrence = cible.getBoundingClientRect();
    zoneDefilante.scrollBy({
      top: occurrence.top - zone.top - (zone.height - occurrence.height) / 2,
      behavior: 'smooth',
    });
  }

  async function modifierLocuteur(identifiant: string, segment: string) {
    const locuteur = locuteurs.find(
      (element) => element.identifiant === identifiant
    );
    if (!locuteur) return;
    segmentLocuteurEnEdition = segment;
    nomLocuteurSaisi = locuteur.nom_affiche ?? '';
    await tick();
    champNomLocuteur?.focus();
    champNomLocuteur?.select();
  }

  function enregistrerNomLocuteur(identifiant: string) {
    const nom = nomLocuteurSaisi.trim();
    const locuteur = locuteurs.find(
      (element) => element.identifiant === identifiant
    );
    segmentLocuteurEnEdition = null;
    if (!locuteur || (locuteur.nom_affiche ?? '') === nom) return;
    const nouveauxLocuteurs = locuteurs.map((element) =>
      element.identifiant === identifiant
        ? { ...element, nom_affiche: nom }
        : element
    );
    onlocuteurs(nouveauxLocuteurs);
    revision += 1;
  }

  function reveiller(valeur: string) {
    valeurRevelee = valeur;
    revision += 1;
  }

  function masquerRevelation() {
    valeurRevelee = null;
    revision += 1;
  }

  function selectionnerTexte() {
    const selection = window.getSelection();
    if (!selection || selection.isCollapsed) return;
    if (
      !conteneur.contains(selection.anchorNode) ||
      !conteneur.contains(selection.focusNode)
    )
      return;
    const plage = selection.getRangeAt(0);
    if (
      [...conteneur.querySelectorAll('[data-locuteur]')].some((element) =>
        plage.intersectsNode(element)
      )
    ) {
      fermerAjoutSelection();
      return;
    }
    const debut = selection.anchorNode?.parentElement?.closest('[data-champ]');
    const fin = selection.focusNode?.parentElement?.closest('[data-champ]');
    if (debut && debut === fin) {
      const valeur = selection.toString();
      if (!valeur.trim()) return;
      texteSelectionne = valeur;
      refusSelection = false;
      plageSelectionnee = plage.cloneRange();
      void positionnerPopup();
    } else {
      fermerAjoutSelection();
    }
  }

  function programmerSelection() {
    if (minuteurSelection !== null) clearTimeout(minuteurSelection);
    minuteurSelection = setTimeout(() => {
      minuteurSelection = null;
      selectionnerTexte();
    }, 120);
  }

  function touche(event: KeyboardEvent) {
    if (event.key === 'Escape') {
      valeurRevelee = null;
      fermerAjoutSelection();
      revision += 1;
    }
  }

  onMount(() => {
    valeurSelectionnee ??= modele.selection;
    onprojection(modele.projeter('transcript'), modele.projeter('contexte'));
    onetat(modele.lireEtat());
    const echapper = (event: KeyboardEvent) => {
      if (conteneur.contains(document.activeElement) || texteSelectionne)
        touche(event);
    };
    document.addEventListener('mouseup', selectionnerTexte);
    document.addEventListener('keyup', selectionnerTexte);
    document.addEventListener('selectionchange', programmerSelection);
    document.addEventListener('keydown', echapper);
    document.addEventListener('scroll', programmerPositionPopup, true);
    window.addEventListener('resize', programmerPositionPopup);
    return () => {
      document.removeEventListener('mouseup', selectionnerTexte);
      document.removeEventListener('keyup', selectionnerTexte);
      document.removeEventListener('selectionchange', programmerSelection);
      document.removeEventListener('keydown', echapper);
      document.removeEventListener('scroll', programmerPositionPopup, true);
      window.removeEventListener('resize', programmerPositionPopup);
      if (minuteurSelection !== null) clearTimeout(minuteurSelection);
      if (framePositionPopup !== null) cancelAnimationFrame(framePositionPopup);
    };
  });
</script>

<section
  class="relecture"
  aria-label="Relecture de la pseudonymisation"
  bind:this={conteneur}
>
  <div class="document">
    <p>
      Survolez ou placez le focus sur un masque pour révéler temporairement son
      original. Cliquez pour basculer toutes ses occurrences. Sélectionnez du texte
      pour afficher l’ajout de masque au-dessus de la sélection.
    </p>
    <ul class="legende" aria-label="Légende des catégories">
      {#each categoriesRelecture as categorie (categorie.id)}
        <li><span class={`pastille ${categorie.id}`}></span>{categorie.label}</li>
      {/each}
    </ul>
    <div class="actions actions-principales" aria-label="Historique et navigation">
      <button type="button" class="fr-btn fr-btn--secondary" onclick={annuler}
        >Annuler</button
      >
      <button type="button" class="fr-btn fr-btn--secondary" onclick={retablir}
        >Rétablir</button
      >
      <button
        type="button"
        class="fr-btn fr-btn--secondary"
        onclick={() => parcourir(-1)}>Occurrence précédente</button
      >
      <button
        type="button"
        class="fr-btn fr-btn--secondary"
        onclick={() => parcourir(1)}>Occurrence suivante</button
      >
    </div>
    <div
      class="zone-defilante"
      bind:this={zoneDefilante}
      role="region"
      aria-label="Transcript et contexte, zone défilante"
    >
      {#each segments as section (section.champ)}
        <article
          class="source"
          aria-label={section.champ === 'transcript' ? 'Transcript' : 'Contexte'}
          data-champ={section.champ}
        >
          <h3>{section.champ === 'transcript' ? 'Transcript' : 'Contexte'}</h3>
          <p class="texte">
            {#each section.morceaux as morceau, index (index)}
              {#if morceau.type === 'texte'}
                {morceau.texte}
              {:else if morceau.type === 'locuteur'}
                {#if segmentLocuteurEnEdition === `${section.champ}-${index}`}
                  <input
                    class="fr-input nom-locuteur"
                    aria-label={'Nom affiché pour ' + morceau.texte}
                    placeholder={morceau.texte}
                    bind:value={nomLocuteurSaisi}
                    bind:this={champNomLocuteur}
                    onblur={() => enregistrerNomLocuteur(morceau.identifiant)}
                    onkeydown={(event) => {
                      if (event.key === 'Enter') {
                        event.preventDefault();
                        event.currentTarget.blur();
                      }
                      if (event.key === 'Escape') {
                        nomLocuteurSaisi =
                          locuteurs.find(
                            (element) => element.identifiant === morceau.identifiant
                          )?.nom_affiche ?? '';
                        segmentLocuteurEnEdition = null;
                      }
                    }}
                  />
                {:else}
                  <button
                    type="button"
                    class="locuteur"
                    data-locuteur={morceau.identifiant}
                    aria-label={'Modifier le nom affiché de ' + morceau.texte}
                    onclick={() =>
                      modifierLocuteur(
                        morceau.identifiant,
                        `${section.champ}-${index}`
                      )}>{morceau.texte}:</button
                  >
                {/if}
              {:else}
                {@const masque = masques.find(
                  (m) => m.identifiant === morceau.identifiant
                )!}
                <button
                  type="button"
                  class="marqueur"
                  class:identite={masque.categorie === 'identite'}
                  class:technologie={masque.categorie === 'technologie_ou_produit'}
                  class:organisation={masque.categorie === 'organisation'}
                  class:secret={masque.categorie === 'secret'}
                  class:coordonnees={masque.categorie === 'coordonnees'}
                  class:donnee_sensible={masque.categorie === 'donnee_sensible'}
                  class:inactif={!masque.actif}
                  class:selectionne={valeurSelectionnee === morceau.identifiant}
                  data-masque={morceau.identifiant}
                  aria-label={masque.actif
                    ? `Occurrence masquée ${masque.valeur_anonyme}`
                    : `Masque désactivé ${masque.valeur_originale}`}
                  onclick={() => basculer(masque.identifiant)}
                  onmouseenter={() => reveiller(masque.valeur_originale)}
                  onmouseleave={masquerRevelation}
                  onfocus={() => reveiller(masque.valeur_originale)}
                  onblur={masquerRevelation}
                  >{masque.valeur_originale}{#if valeurRevelee === masque.valeur_originale}<span
                      class="original"
                      role="status">{masque.valeur_originale}</span
                    >{/if}</button
                >
              {/if}
            {/each}
          </p>
        </article>
      {/each}
    </div>
  </div>
  {#if texteSelectionne}
    <div
      class="selection-popover"
      class:selection-popover-erreur={refusSelection}
      bind:this={popupSelection}
      role="group"
      aria-label="Créer un masque depuis la sélection"
      style:left={`${positionPopup?.gauche ?? 0}px`}
      style:top={`${positionPopup?.haut ?? 0}px`}
      style:visibility={positionPopup ? 'visible' : 'hidden'}
    >
      <p class="texte-selectionne">
        <strong>Texte à masquer</strong>
        <span>« {texteSelectionne} »</span>
      </p>
      <div class="commandes-selection">
        <div class="choix-categories" role="group" aria-label="Catégorie">
          {#each categoriesRelecture as categorie (categorie.id)}
            <button
              type="button"
              class="choix-categorie"
              class:choisi={categorieSelection === categorie.id}
              aria-pressed={categorieSelection === categorie.id}
              onclick={() => (categorieSelection = categorie.id)}
            >
              <span class={`pastille ${categorie.id}`}></span>{categorie.label}
            </button>
          {/each}
        </div>
        <div class="actions-selection">
          <button type="button" class="fr-btn" onclick={ajouterSelection}
            >Masquer toutes les occurrences</button
          >
          <button
            type="button"
            class="fr-btn fr-btn--secondary"
            onclick={fermerAjoutSelection}>Annuler</button
          >
        </div>
      </div>
      {#if refusSelection}<p class="erreur" role="alert">
          Cette sélection chevauche un masque existant. Sélectionnez ce masque pour
          le modifier.
        </p>{/if}
    </div>
  {/if}
  <aside class="panneau" aria-label="Détail du masque sélectionné">
    <h2>Masque sélectionné</h2>
    <p>
      {masques.length
        ? `${indexSelection + 1} sur ${masques.length}`
        : 'Aucun masque détecté'}
    </p>
    {#if masqueSelectionne}
      <p class="original-selectionne">
        Valeur d’origine : <strong>{masqueSelectionne.valeur_originale}</strong>
      </p>
      <label
        >Catégorie<select
          class="fr-select"
          value={masqueSelectionne.categorie}
          onchange={categoriser}
          >{#each categoriesRelecture as categorie (categorie.id)}<option
              value={categorie.id}>{categorie.label}</option
            >{/each}</select
        ></label
      >
      <div class="actions">
        <button
          type="button"
          class="fr-btn fr-btn--secondary"
          onclick={() => reveiller(masqueSelectionne.valeur_originale)}
          >Révéler</button
        >
        <button
          type="button"
          class="fr-btn fr-btn--secondary"
          disabled={masqueSelectionne.impose && masqueSelectionne.actif}
          onclick={() => basculer(masqueSelectionne.identifiant)}
          >{masqueSelectionne.impose
            ? 'Masque obligatoire — liste noire'
            : masqueSelectionne.actif
              ? 'Désactiver'
              : 'Activer'}</button
        >
      </div>
      {#if messageMasqueObligatoire}<p role="alert">
          {messageMasqueObligatoire}
        </p>{/if}
      <p>
        {compteSelection} occurrences · {masqueSelectionne.actif
          ? masqueSelectionne.valeur_anonyme
          : 'Masque désactivé'}
      </p>
    {/if}
  </aside>
</section>

<style>
  .relecture {
    display: grid;
    grid-template-columns: minmax(0, 3fr) minmax(16rem, 1fr);
    gap: 1rem;
    align-items: start;
  }
  .document,
  .panneau {
    min-width: 0;
  }
  .panneau h2 {
    font-size: 1.25rem;
    line-height: 1.5rem;
  }
  .legende {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem 1rem;
    padding: 0;
    list-style: none;
  }
  .legende li {
    display: flex;
    align-items: center;
    gap: 0.35rem;
  }
  .pastille {
    width: 0.75rem;
    height: 0.75rem;
    border-radius: 0.15rem;
    background: #7041a6;
  }
  .pastille.identite {
    background: #18753c;
  }
  .pastille.organisation {
    background: #6b4f00;
  }
  .pastille.secret {
    background: #a33a2b;
  }
  .pastille.coordonnees {
    background: #7041a6;
  }
  .pastille.donnee_sensible {
    background: #006a6a;
  }
  .pastille.technologie_ou_produit {
    background: #0063cb;
  }
  .panneau {
    position: sticky;
    top: 1rem;
    max-height: 75vh;
    overflow: auto;
    border: 1px solid var(--border-default-grey);
    padding: 1rem;
  }
  .selection-popover {
    position: fixed;
    z-index: 10;
    width: min(36rem, calc(100vw - 1rem));
    box-sizing: border-box;
    padding: 0.75rem;
    border: 2px solid var(--border-active-blue-france);
    background: var(--background-default-grey);
    box-shadow: 0 4px 16px #0003;
  }
  .texte-selectionne {
    display: grid;
    gap: 0.2rem;
    margin: 0 0 0.6rem;
    overflow-wrap: anywhere;
  }
  .texte-selectionne span {
    max-height: 5rem;
    overflow: auto;
  }
  .commandes-selection {
    display: grid;
    grid-template-columns: minmax(0, 1fr) auto;
    align-items: center;
    gap: 0.75rem;
  }
  .choix-categories {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 0.25rem;
  }
  .choix-categorie {
    display: flex;
    align-items: center;
    gap: 0.3rem;
    min-width: 0;
    min-height: 2rem;
    padding: 0.2rem 0.3rem;
    border: 1px solid transparent;
    background: transparent;
    color: var(--text-default-grey);
    font: inherit;
    font-size: 0.8rem;
    line-height: 1.1rem;
    text-align: left;
    cursor: pointer;
  }
  .choix-categorie.choisi {
    border-color: var(--border-active-blue-france);
    background: var(--background-contrast-info);
    font-weight: 700;
  }
  .choix-categorie:focus-visible {
    outline: 2px solid var(--border-active-blue-france);
    outline-offset: 2px;
  }
  .choix-categorie .pastille {
    flex: 0 0 0.65rem;
    width: 0.65rem;
    height: 0.65rem;
  }
  .actions-selection {
    display: grid;
    justify-items: stretch;
    gap: 0.35rem;
  }
  .actions-selection .fr-btn {
    white-space: normal;
  }
  .selection-popover-erreur {
    border-color: var(--border-plain-error);
  }
  .source {
    border: 1px solid var(--border-default-grey);
    padding: 1rem;
    margin-block: 1rem;
  }
  .zone-defilante {
    max-height: min(70vh, 54rem);
    overflow-y: auto;
    overscroll-behavior: contain;
    scroll-behavior: smooth;
    scrollbar-gutter: stable;
  }
  .texte {
    white-space: pre-wrap;
    overflow-wrap: anywhere;
    line-height: 1.7;
    user-select: text;
  }
  .locuteur {
    border: 1px solid var(--border-default-grey);
    border-inline-start: 0.25rem solid var(--border-action-high-blue-france);
    border-radius: 0.2rem;
    padding: 0 0.25rem;
    color: var(--text-title-blue-france);
    background: var(--background-contrast-info);
    font: inherit;
    font-weight: 700;
    cursor: pointer;
    user-select: none;
  }
  .locuteur:hover {
    text-decoration: underline;
  }
  .locuteur:focus-visible {
    outline: 2px solid var(--border-active-blue-france);
    outline-offset: 2px;
  }
  .nom-locuteur {
    display: inline-block;
    width: min(16rem, 70vw);
    margin-inline-end: 0.25rem;
    padding: 0.125rem 0.375rem;
    vertical-align: baseline;
  }
  .marqueur {
    position: relative;
    border: 1px solid currentColor;
    border-radius: 0.2rem;
    padding: 0 0.12rem;
    color: #7041a6;
    background: var(--background-default-grey);
    font: inherit;
    cursor: pointer;
  }
  .marqueur:not(.inactif) {
    color: transparent;
    border-color: transparent;
    background: #7041a6;
  }
  .marqueur.donnee_sensible {
    color: #006a6a;
  }
  .marqueur.donnee_sensible:not(.inactif) {
    color: transparent;
    background: #006a6a;
  }
  .marqueur.identite {
    color: #18753c;
  }
  .marqueur.identite:not(.inactif) {
    color: transparent;
    background: #18753c;
  }
  .marqueur.organisation {
    color: #6b4f00;
  }
  .marqueur.organisation:not(.inactif) {
    color: transparent;
    background: #6b4f00;
  }
  .marqueur.secret {
    color: #a33a2b;
  }
  .marqueur.secret:not(.inactif) {
    color: transparent;
    background: #a33a2b;
  }
  .marqueur.coordonnees {
    color: #7041a6;
  }
  .marqueur.coordonnees:not(.inactif) {
    color: transparent;
    background: #7041a6;
  }
  .marqueur.technologie {
    color: #0063cb;
  }
  .marqueur.technologie:not(.inactif) {
    color: transparent;
    background: #0063cb;
  }
  .marqueur.inactif {
    text-decoration: underline dashed;
  }
  .marqueur.selectionne,
  .panneau {
    outline: 2px solid var(--border-active-blue-france);
  }
  .original {
    position: absolute;
    z-index: 2;
    inset: 0 auto auto 0;
    width: max-content;
    max-width: min(30rem, 80vw);
    padding: 0 0.12rem;
    color: var(--text-inverted-blue-france);
    background: var(--background-action-high-blue-france);
    white-space: nowrap;
    box-shadow: 0 2px 8px #0003;
  }
  .original-selectionne {
    padding: 0.75rem;
    background: var(--background-alt-grey);
  }
  .panneau label {
    display: block;
    margin-block: 0.4rem;
  }
  .actions {
    display: flex;
    flex-wrap: wrap;
    gap: 0.4rem;
    margin-block: 0.5rem;
  }
  .actions-principales {
    position: sticky;
    z-index: 2;
    top: 0;
    padding-block: 0.5rem;
    background: var(--background-default-grey);
  }
  @media (max-width: 48rem) {
    .relecture {
      grid-template-columns: 1fr;
    }
    .zone-defilante {
      max-height: 60vh;
    }
    .panneau {
      position: static;
      max-height: none;
      grid-row: 2;
    }
  }
  @media (max-width: 36rem) {
    .commandes-selection {
      grid-template-columns: 1fr;
    }
    .choix-categories {
      grid-template-columns: repeat(2, minmax(0, 1fr));
    }
    .actions-selection {
      grid-template-columns: 1fr auto;
      align-items: center;
    }
  }
</style>
