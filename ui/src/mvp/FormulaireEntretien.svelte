<script lang="ts">
  let {
    participant = $bindable(''),
    date_entretien = $bindable(''),
    moderateur = $bindable(''),
    contenu = $bindable(''),
    note_moderateur = $bindable(''),
    compact = false,
  }: {
    participant: string;
    date_entretien: string;
    moderateur: string;
    contenu: string;
    note_moderateur: string;
    compact?: boolean;
  } = $props();
</script>

<label class:compact>
  Prénom de l’utilisateur
  <input class="fr-input" required bind:value={participant} />
</label>
<label class:compact>
  Date de l’entretien
  <input class="fr-input" required type="date" bind:value={date_entretien} />
</label>
<label class:compact>
  Modérateur
  <input class="fr-input" required bind:value={moderateur} />
</label>
<label class:compact>
  Transcript de l’entretien
  <textarea class="fr-input" class:compact required bind:value={contenu}></textarea>
</label>
<label class:compact>
  Note du modérateur
  <textarea class="fr-input" class:compact bind:value={note_moderateur}></textarea>
</label>

<style>
  label {
    display: block;
    margin: 1.5rem 0;
    max-width: var(--largeur-saisie, 32rem);
  }
  input,
  textarea {
    display: block;
    margin-top: 0.5rem;
  }
  textarea {
    min-height: 8rem;
  }
  label.compact {
    margin: 1rem 0;
  }
  textarea.compact {
    min-height: 5rem;
  }
</style>
