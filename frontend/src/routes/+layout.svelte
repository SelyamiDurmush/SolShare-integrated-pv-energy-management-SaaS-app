<script lang="ts">
  import "../app.css";
  let { children } = $props();
</script>

<!-- This is the layout component for the application, it is the root component
that wraps all other components -->
{@render children()}
