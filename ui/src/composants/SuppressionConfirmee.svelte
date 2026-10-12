<script lang="ts">
  type ApiDsfr = (element: HTMLElement) => {
    modal: { conceal: () => void };
  };

  let {
    modalId,
    titre,
    description,
    onconfirmer,
    onsucces,
  }: {
    modalId: string;
    titre: string;
    description: string;
    onconfirmer: () => Promise<void>;
    onsucces: () => void;
  } = $props();
  let dialogue: HTMLDialogElement;
  let saisie = $state('');
  let enCours = $state(false);
  let erreur = $state('');

  async function confirmer() {
    if (saisie !== 'JE CONFIRME' || enCours) return;
    enCours = true;
    erreur = '';
    try {
      await onconfirmer();
      const dsfr = (window as unknown as { dsfr?: ApiDsfr }).dsfr;
      if (dsfr) dsfr(dialogue).modal.conceal();
      else dialogue.close();
      enCours = false;
      onsucces();
    } catch (cause) {
      erreur = cause instanceof Error ? cause.message : 'La suppression a échoué.';
    } finally {
      enCours = false;
    }
  }
</script>

<button
  class="fr-btn fr-btn--secondary fr-btn--sm fr-icon-delete-line fr-btn--icon-left"
  type="button"
  aria-controls={modalId}
  aria-label={titre}
  data-fr-opened="false">Supprimer</button
>

<dialog
  bind:this={dialogue}
  id={modalId}
  class="fr-modal"
  aria-labelledby={`${modalId}-titre`}
  data-fr-concealing-backdrop="false"
  oncancel={(event) => {
    if (enCours) event.preventDefault();
  }}
  onclose={() => {
    saisie = '';
    erreur = '';
  }}
>
  <div class="fr-container fr-container--fluid fr-container-md">
    <div class="fr-grid-row fr-grid-row--center">
      <div class="fr-col-12 fr-col-md-8 fr-col-lg-6">
        <div class="fr-modal__body">
          <div class="fr-modal__header">
            <button
              class="fr-btn--close fr-btn"
              type="button"
              aria-controls={modalId}
              data-fr-close
              disabled={enCours}>Fermer</button
            >
          </div>
          <div class="fr-modal__content">
            <h2 class="fr-modal__title" id={`${modalId}-titre`}>{titre}</h2>
            <p>{description}</p>
            <div class="fr-input-group" class:fr-input-group--error={erreur}>
              <label class="fr-label" for={`${modalId}-confirmation`}>
                Saisissez exactement JE CONFIRME pour confirmer
              </label>
              <input
                class="fr-input"
                id={`${modalId}-confirmation`}
                bind:value={saisie}
                autocomplete="off"
                disabled={enCours}
              />
              {#if erreur}<p class="fr-error-text" role="alert">{erreur}</p>{/if}
            </div>
            {#if enCours}<p role="status" aria-live="polite">
                Suppression en cours…
              </p>{/if}
          </div>
          <div class="fr-modal__footer">
            <ul
              class="fr-btns-group fr-btns-group--right fr-btns-group--inline-reverse fr-btns-group--inline-sm"
            >
              <li>
                <button
                  class="fr-btn"
                  type="button"
                  disabled={saisie !== 'JE CONFIRME' || enCours}
                  onclick={confirmer}>Supprimer définitivement</button
                >
              </li>
              <li>
                <button
                  class="fr-btn fr-btn--secondary"
                  type="button"
                  aria-controls={modalId}
                  data-fr-close
                  disabled={enCours}>Annuler</button
                >
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  </div>
</dialog>
