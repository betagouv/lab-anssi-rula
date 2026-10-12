<script lang="ts">
  let { contenu }: { contenu: Record<string, unknown> } = $props();
</script>

<section aria-live="polite">
  <h2>Résumé</h2>
  <p>{String(contenu.resume ?? '')}</p>
  {#if Array.isArray(contenu.themes)}
    <h2>Thèmes</h2>
    <ul>
      {#each contenu.themes as theme, index (index)}<li>{String(theme)}</li>{/each}
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
                    {String('speaker_id' in element ? element.speaker_id : '')}, tour {String(
                      'tour_id' in element ? element.tour_id : ''
                    )}
                  </footer>
                </blockquote>{/if}
              {#if 'sentiment' in element}<p>
                  Sentiment : {String(element.sentiment)}
                </p>
                {#if 'gravite' in element && element.gravite}<p>
                    Gravité : {String(element.gravite)}
                  </p>{/if}{/if}
            {/if}
          </li>
        {/each}
      </ul>
    {/if}
  {/each}
</section>

<style>
  h2 {
    margin-top: 2rem;
  }
  .extractions {
    padding-left: 1.5rem;
  }
  blockquote {
    border-left: 0.25rem solid var(--border-default-grey);
    margin: 1rem 0;
    padding-left: 1rem;
  }
  footer {
    color: var(--text-mention-grey);
  }
</style>
