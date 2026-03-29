<script lang="ts">
  let { title = '', className = '', children } = $props();
</script>

<div class="rounded-xl border border-gray-200 dark:border-gray-800 bg-white/70 dark:bg-gray-900/50 backdrop-blur-md p-6 shadow-xl transition-colors duration-300 {className}">
  {#if title}
    <h3 class="mb-4 text-xl font-bold tracking-tight text-gray-900 dark:text-white">{title}</h3>
  {/if}
  {@render children()}
</div>
