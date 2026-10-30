<script lang="ts">
  type ApiDsfr = (element: HTMLElement) => {
    modal: { conceal: () => void };
  };

  let {
    modalId,
    confirmationNecessaire,
    desactive,
    enCours,
    erreur,
    onconfirmer,
  }: {
    modalId: string;
    confirmationNecessaire: boolean;
    desactive: boolean;
    enCours: boolean;
    erreur: string;
    onconfirmer: () => Promise<boolean>;
  } = $props();
  let dialogue: HTMLDialogElement;

  function ouvrirSansDsfr() {
    const dsfr = (window as unknown as { dsfr?: ApiDsfr }).dsfr;
    if (!dsfr && !dialogue.open) dialogue.showModal();
  }

  function enregistrerSansConfirmation() {
    void onconfirmer();
  }

  function fermer() {
    const dsfr = (window as unknown as { dsfr?: ApiDsfr }).dsfr;
    if (dsfr && dialogue.open) dsfr(dialogue).modal.conceal();
    else if (dialogue.open) dialogue.close();
  }

  async function confirmer() {
    if (enCours) return;
    if (await onconfirmer()) fermer();
  }
</script>

<button
  class="fr-btn"
  type="button"
  aria-controls={modalId}
  aria-haspopup={confirmationNecessaire ? 'dialog' : undefined}
  data-fr-opened={confirmationNecessaire ? 'false' : undefined}
  disabled={desactive}
  onclick={confirmationNecessaire ? ouvrirSansDsfr : enregistrerSansConfirmation}
  >Valider et enregistrer</button
>

<dialog
  bind:this={dialogue}
  id={modalId}
  class="fr-modal"
  aria-labelledby={`${modalId}-titre`}
  aria-describedby={`${modalId}-description`}
  data-fr-concealing-backdrop="false"
  oncancel={(event) => {
    if (enCours) event.preventDefault();
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
            <h2 class="fr-modal__title" id={`${modalId}-titre`}>
              Confirmer la pseudonymisation définitive
            </h2>
            <p id={`${modalId}-description`}>
              Après confirmation, le transcript et le contexte pseudonymisés seront
              enregistrés. Les correspondances entre les valeurs d’origine et leurs
              libellés ne seront pas conservées : vous ne pourrez plus révéler ni
              décaviarder les éléments masqués. Les termes de la liste noire restent
              associés à la source pour protéger ses futures modifications.
            </p>
            {#if erreur}<p class="fr-error-text" role="alert">{erreur}</p>{/if}
            {#if enCours}<p role="status" aria-live="polite">Enregistrement…</p>{/if}
          </div>
          <div class="fr-modal__footer">
            <ul
              class="fr-btns-group fr-btns-group--right fr-btns-group--inline-reverse fr-btns-group--inline-sm"
            >
              <li>
                <button
                  class="fr-btn"
                  type="button"
                  disabled={desactive || enCours}
                  onclick={confirmer}>Confirmer et enregistrer</button
                >
              </li>
              <li>
                <button
                  class="fr-btn fr-btn--secondary"
                  type="button"
                  aria-controls={modalId}
                  data-fr-close
                  disabled={enCours}>Retour à la relecture</button
                >
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  </div>
</dialog>
