<script lang="ts">
  import Button from '$lib/components/ui/Button.svelte';
  
  let allocationMethod = $state('dynamic');
</script>

<div class="space-y-6 max-w-4xl">
  <div>
    <h1 class="text-3xl font-bold tracking-tight text-gray-900 dark:text-white mb-2 transition-colors">Settings</h1>
    <p class="text-gray-600 dark:text-gray-400 transition-colors">System preferences and global configuration.</p>
  </div>

  <div class="bg-white dark:bg-gray-900/50 rounded-xl border border-gray-200 dark:border-gray-800 shadow-sm overflow-hidden transition-colors">
    <div class="p-6">
      <h2 class="text-xl font-bold text-gray-900 dark:text-white mb-2 transition-colors">Energy Allocation</h2>
      <p class="text-sm text-gray-500 dark:text-gray-400 mb-6 transition-colors">
        Configure how solar energy is distributed among residents. This setting applies to all new billing cycles.
      </p>

      <div class="mb-4">
        <label for="allocation" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 transition-colors">Allocation Method</label>
        <select 
          id="allocation" 
          bind:value={allocationMethod}
          class="w-full max-w-md bg-gray-50 dark:bg-black border border-gray-200 dark:border-gray-700 text-gray-900 dark:text-gray-100 rounded-lg py-2.5 px-3 outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent transition-colors appearance-none"
        >
          <option value="dynamic">Dynamic (Real-time Consumption)</option>
          <option value="static">Static (Flat Percentage)</option>
        </select>
      </div>

      <p class="text-sm text-gray-500 dark:text-gray-400 mb-6 transition-colors">
        Refer to German Energy Industry Act, Section 42b for compliance details.
      </p>

      <button class="px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white font-medium rounded-md transition-colors shadow-sm">
        Save Changes
      </button>
    </div>
  </div>
</div>
