<script lang="ts">
  let { contenu }: { contenu: Record<string, unknown> } = $props();
  const produit = $derived(
    typeof contenu.contexte === 'object' && contenu.contexte !== null
  );
  const texte = (valeur: unknown) => (typeof valeur === 'string' ? valeur : '');
  const liste = (cle: string) =>
    Array.isArray(contenu[cle]) ? (contenu[cle] as Record<string, unknown>[]) : [];
  const contexte = $derived(
    produit ? (contenu.contexte as Record<string, unknown>) : {}
  );
  const nature = (valeur: unknown) =>
    ({ fait: 'Fait', hypothese: 'Hypothèse', interpretation: 'Interprétation' })[
      texte(valeur)
    ] ?? '';
  const origine = (valeur: unknown) =>
    ({
      demande_utilisateur: 'Demande utilisateur',
      proposition_analyste: 'Proposition de l’analyste',
    })[texte(valeur)] ?? '';
</script>

<section aria-live="polite">
  {#if produit}
    <h2>Synthèse</h2>
    <p>{texte(contenu.ouverture)}</p>
    {#if Array.isArray(contenu.points_cles) && contenu.points_cles.length}
      <ol>
        {#each contenu.points_cles as point, index (`point-${index}`)}<li>
            {texte(point)}
          </li>{/each}
      </ol>
    {/if}
    <h2>Contexte</h2>
    <dl>
      {#each [['Produit', 'produit'], ['Profil utilisateur', 'profil_utilisateur'], ['Objectif', 'objectif']] as [libelle, cle] (cle)}
        {#if texte(contexte[cle])}<dt>{libelle}</dt>
          <dd>{texte(contexte[cle])}</dd>{/if}
      {/each}
    </dl>
    {#if liste('profil').length}
      <h2>Profil factuel</h2>
      <ul>
        {#each liste('profil') as fait, index (`profil-${index}`)}
          <li>
            <p>{texte(fait.description)}</p>
          </li>
        {/each}
      </ul>
    {/if}
    {#if liste('sujets').length}
      <h2>Sujets détaillés</h2>
      {#each liste('sujets') as sujet, index (`sujet-${index}`)}
        <article>
          <h3>{index + 1}. {texte(sujet.titre)}</h3>
          <p>{texte(sujet.constat)}</p>
          {#if Array.isArray(sujet.enseignements)}
            <ul>
              {#each sujet.enseignements as enseignement, i (`enseignement-${index}-${i}`)}
                <li>
                  <strong>{nature(enseignement.nature)} :</strong>
                  {texte(enseignement.description)}
                  {#if texte(enseignement.verbatim)}
                    <blockquote>
                      « {texte(enseignement.verbatim)} »
                      <footer>
                        {texte(enseignement.speaker_id)}, tour {String(
                          enseignement.tour_id
                        )}
                      </footer>
                    </blockquote>
                  {/if}
                </li>
              {/each}
            </ul>
          {/if}
        </article>
      {/each}
    {/if}
    {#if liste('pistes').length}
      <h2>Pistes à valider</h2>
      <p>L’effort est une estimation à valider par l’équipe.</p>
      <table class="tableau-pistes">
        <thead
          ><tr
            ><th scope="col">Action</th><th scope="col">Besoin et origine</th><th
              scope="col">Effort estimé</th
            ></tr
          ></thead
        >
        <tbody>
          {#each liste('pistes') as piste, index (`piste-${index}`)}
            <tr
              ><td>{texte(piste.action)}</td><td
                >{texte(piste.besoin)}<small
                  >Origine : {origine(piste.origine)}</small
                ></td
              ><td>{texte(piste.effort_estime)}</td></tr
            >
          {/each}
        </tbody>
      </table>
    {/if}
    {#if liste('prochaines_etapes').length}
      <h2>Prochaines étapes</h2>
      <ul>
        {#each liste('prochaines_etapes') as etape, index (`etape-${index}`)}
          <li>
            {texte(etape.action)}
            <span>À vérifier : {texte(etape.verification)}</span>
            {#if texte(etape.verbatim)}
              <blockquote>
                « {texte(etape.verbatim)} »
                <footer>
                  {texte(etape.speaker_id)}, tour {String(etape.tour_id)}
                </footer>
              </blockquote>
            {/if}
          </li>
        {/each}
      </ul>
    {/if}
  {:else}
    <h2>Résumé</h2>
    <p>{texte(contenu.resume)}</p>
    {#if Array.isArray(contenu.themes)}
      <h2>Thèmes</h2>
      <ul>
        {#each contenu.themes as theme, index (index)}<li>{texte(theme)}</li>{/each}
      </ul>
    {/if}
    {#each Object.entries(contenu) as [cle, elements] (cle)}
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
                {#if 'type' in element}<p>Type : {texte(element.type)}</p>{/if}
                <p>
                  {texte(
                    'description' in element
                      ? element.description
                      : 'action' in element
                        ? element.action
                        : ''
                  )}
                </p>
                {#if 'verbatim' in element}<blockquote>
                    « {texte(element.verbatim)} »
                    <footer>
                      {texte('speaker_id' in element ? element.speaker_id : '')},
                      tour {String('tour_id' in element ? element.tour_id : '')}
                    </footer>
                  </blockquote>{/if}
                {#if 'sentiment' in element}<p>
                    Sentiment : {texte(element.sentiment)}
                  </p>{/if}
                {#if 'gravite' in element && element.gravite}<p>
                    Gravité : {texte(element.gravite)}
                  </p>{/if}
              {/if}
            </li>
          {/each}
        </ul>
      {/if}
    {/each}
  {/if}
</section>

<style>
  h2 {
    margin-top: 2rem;
  }
  h3 {
    margin-top: 1.5rem;
  }
  dl {
    display: grid;
    grid-template-columns: max-content 1fr;
    gap: 0.5rem 1rem;
  }
  .tableau-pistes {
    border-collapse: collapse;
    width: 100%;
  }
  .tableau-pistes th,
  .tableau-pistes td {
    border-bottom: 1px solid var(--border-default-grey);
    padding: 0.75rem;
    text-align: left;
    vertical-align: top;
  }
  .tableau-pistes small {
    display: block;
    color: var(--text-mention-grey);
  }
  dt {
    font-weight: 700;
  }
  .extractions {
    padding-left: 1.5rem;
  }
  blockquote {
    border-left: 0.25rem solid var(--border-default-grey);
    margin: 1rem 0;
    padding-left: 1rem;
  }
  footer,
  span {
    color: var(--text-mention-grey);
  }
  @media (max-width: 40rem) {
    .tableau-pistes th,
    .tableau-pistes td {
      padding: 0.5rem 0.25rem;
    }
  }
</style>
