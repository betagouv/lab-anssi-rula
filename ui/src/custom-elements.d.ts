import 'svelte/elements';

declare module 'svelte/elements' {
  interface SvelteHTMLElements {
    'dsfr-select': {
      id?: string;
      label?: string;
      options?: { value: string; label: string }[] | string;
      value?: string;
      required?: string;
      hint?: string;
      disabled?: string;
      placeholder?: string;
      onvaluechanged?: (e: CustomEvent<string>) => void;
    };
    'dsfr-input': {
      id?: string;
      label?: string;
      type?: string;
      value?: string;
      required?: string;
      disabled?: string;
      placeholder?: string;
      hint?: string;
      onvaluechanged?: (e: CustomEvent<string>) => void;
    };
    'dsfr-textarea': {
      id?: string;
      label?: string;
      value?: string;
      rows?: number | string;
      required?: string;
      disabled?: string;
      onvaluechanged?: (e: CustomEvent<string>) => void;
    };
    'dsfr-button': {
      label?: string;
      kind?: string;
      type?: string;
      disabled?: string;
      onclick?: (e: MouseEvent) => void;
    };
  }
}
