<script lang="ts">
  let { confirme = $bindable(false) }: { confirme: boolean } = $props();
</script>

<section class="guide">
  <h2>Vérifiez le transcript avant de l’enregistrer</h2>
  <p>
    Seul le transcript est vérifié par le garde-fou avant son enregistrement. Ne
    transmettez qu’un transcript préparé pour cet usage.
  </p>
  <h3>Guide de préparation</h3>
  <ol>
    <li>
      <strong>Anonymisez les personnes et les organisations.</strong> Remplacez les noms,
      adresses e-mail, numéros de téléphone, noms d’entreprise et tout élément permettant
      d’identifier quelqu’un par un terme générique, comme « une participante » ou « une
      collectivité ».
    </li>
    <li>
      <strong>Désensibilisez le contenu.</strong> Retirez les identifiants, liens internes,
      données d’accès, informations de sécurité, données personnelles et tout détail qui
      ne serait pas nécessaire pour comprendre le besoin exprimé.
    </li>
    <li>
      <strong>Généralisez les technologies et les produits.</strong> Ne citez aucun nom
      de logiciel, de service, d’équipement ou de produit. Utilisez par exemple « un outil
      de visioconférence » ou « une solution métier ». Ces précisions pourraient faciliter
      une attaque ciblée.
    </li>
  </ol>
  <p>
    Ces vérifications concernent uniquement le transcript. Les autres champs sont des
    métadonnées de l’entretien et ne sont pas analysés par le garde-fou.
  </p>
  <label
    ><input type="checkbox" bind:checked={confirme} /> Je confirme avoir anonymisé et désensibilisé
    le transcript, et retiré les noms de technologies et de produits.</label
  >
</section>

<style>
  .guide {
    background: var(--background-contrast-blue-france);
    border-left: 0.25rem solid var(--border-action-high-blue-france);
    box-sizing: border-box;
    margin-top: 1.5rem;
    max-width: var(--largeur-saisie, 32rem);
    padding: 1rem 1.25rem;
    width: 100%;
  }
  h2 {
    font-size: 1rem;
    margin: 0 0 0.5rem;
  }
  h3 {
    font-size: 1rem;
    margin: 1.25rem 0 0.5rem;
  }
  p {
    margin: 0 0 1rem;
  }
  ol {
    margin: 0 0 1rem;
    padding-left: 1.5rem;
  }
  li + li {
    margin-top: 0.75rem;
  }
</style>
