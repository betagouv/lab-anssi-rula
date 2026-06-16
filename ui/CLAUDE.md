# CLAUDE.md — Frontend

## Svelte 5 — syntaxe runes uniquement

```svelte
<script lang="ts">
  // ✅ Svelte 5
  let count = $state(0);
  let doubled = $derived(count * 2);

  // ❌ Svelte 4 — ne pas utiliser
  // let count = 0;
  // $: doubled = count * 2;
</script>
```

## Appels API

Le proxy Vite redirige `/api/*` vers `http://backend:3001`. Toujours utiliser des chemins relatifs :

```typescript
const res = await fetch('/api/sante'); // ✅
const res = await fetch('http://localhost:3001/api/sante'); // ❌
```

## Contrôles avant commit

```bash
pnpm lint:check     # ESLint — zéro warning toléré
pnpm format:check   # Prettier
pnpm svelte:check   # Types Svelte + TypeScript
pnpm test           # vitest
```
