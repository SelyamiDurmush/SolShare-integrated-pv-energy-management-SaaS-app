<script lang="ts">
  import type { Snippet } from 'svelte';

  interface Props {
    href?: string;
    variant?: 'primary' | 'secondary' | 'outline';
    className?: string;
    onclick?: (e: MouseEvent) => void;
    type?: 'button' | 'submit' | 'reset';
    disabled?: boolean;
    children: Snippet;
  }

  let { href = undefined, variant = 'primary', className = '', onclick, type = 'button', disabled = false, children }: Props = $props();
  
  const baseClass = "px-4 py-2 font-semibold transition-all duration-300 rounded-lg active:scale-95";
  const variants = {
    primary: "bg-blue-600 text-white hover:bg-blue-700 shadow-lg shadow-blue-500/30 disabled:opacity-50",
    secondary: "bg-gray-800 text-gray-200 hover:bg-gray-700 hover:text-white border border-gray-700",
    outline: "bg-transparent border border-blue-600 text-blue-600 hover:bg-blue-600/10"
  };
</script>

{#if href}
  <a {href} class="{baseClass} {variants[variant]} {className}">
    {@render children()}
  </a>
{:else}
  <button {type} {disabled} {onclick} class="{baseClass} {variants[variant]} {className}">
    {@render children()}
  </button>
{/if}

