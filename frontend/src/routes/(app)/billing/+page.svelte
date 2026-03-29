<script lang="ts">
  import Card from '$lib/components/ui/Card.svelte';
  import Button from '$lib/components/ui/Button.svelte';
  import { FileText, Download, CheckCircle2 } from 'lucide-svelte';
  import { onMount } from 'svelte';
  import { userState } from '$lib/user.svelte';

  let bills = $state<any[]>([]);
  let isLoading = $state(true);
  let currentUser = $derived(userState.profile);

  onMount(async () => {
    isLoading = true;
    try {
      const token = localStorage.getItem('access_token');
      const res = await fetch('http://127.0.0.1:8000/api/v1/billing/statements', {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        bills = await res.json();
      }
    } finally {
      isLoading = false;
    }
  });
</script>

<div class="space-y-6">
  <div class="flex justify-between items-center">
    <div>
      <h1 class="text-3xl font-bold tracking-tight text-gray-900 dark:text-white mb-2 transition-colors">Billing & Allocation</h1>
      <p class="text-gray-600 dark:text-gray-400 transition-colors">Rolling 30-day estimated bills and energy distributions.</p>
    </div>
    {#if currentUser?.role !== 'resident'}
      <Button variant="primary">Generate Bills</Button>
    {/if}
  </div>

  <Card title="Current Period Overview (Last 30 Days)">
    <div class="overflow-x-auto mt-4">
      <table class="w-full text-left border-collapse">
        <thead>
          <tr class="border-b border-gray-200 dark:border-gray-800 text-gray-500 dark:text-gray-400 text-sm transition-colors">
            <th class="py-3 px-4 font-medium">Building</th>
            <th class="py-3 px-4 font-medium">Apartment</th>
            <th class="py-3 px-4 font-medium">Resident</th>
            <th class="py-3 px-4 font-medium text-right">Consumption</th>
            <th class="py-3 px-4 font-medium text-right">Solar Output</th>
            <th class="py-3 px-4 font-medium text-right">Residual</th>
            <th class="py-3 px-4 font-medium text-right">Total Cost</th>
            <th class="py-3 px-4 font-medium text-center">Status</th>
            <th class="py-3 px-4 font-medium"></th>
          </tr>
        </thead>
        <tbody class="text-sm divide-y divide-gray-200 dark:divide-gray-800 transition-colors">
          {#if isLoading}
            <tr>
              <td colspan="9" class="py-8 text-center text-gray-500">Loading statements...</td>
            </tr>
          {:else if bills.length === 0}
            <tr>
              <td colspan="9" class="py-8 text-center text-gray-500">No billing statements available for this period.</td>
            </tr>
          {:else}
            {#each bills as bill}
              <tr class="hover:bg-gray-50 dark:hover:bg-gray-800/30 transition-colors">
                <td class="py-3 px-4 text-gray-600 dark:text-gray-400">{bill.building_name}</td>
                <td class="py-3 px-4 font-medium text-gray-800 dark:text-gray-200">{bill.unit}</td>
                <td class="py-3 px-4 text-gray-600 dark:text-gray-400">{bill.resident}</td>
                <td class="py-3 px-4 text-right text-gray-700 dark:text-gray-300">{bill.consumption} kWh</td>
                <td class="py-3 px-4 text-right text-emerald-600 dark:text-emerald-400 font-medium">{bill.solar_output} kWh</td>
                <td class="py-3 px-4 text-right text-amber-600 dark:text-amber-500">{bill.residual} kWh</td>
                <td class="py-3 px-4 text-right font-bold text-gray-900 dark:text-white">€{bill.total_cost.toFixed(2)}</td>
                <td class="py-3 px-4 text-center">
                  {#if bill.status === 'Paid'}
                    <span class="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-emerald-100 text-emerald-700 border border-emerald-200 dark:bg-emerald-500/10 dark:text-emerald-400 dark:border-emerald-500/20">
                      <CheckCircle2 class="w-3 h-3 mr-1" /> Paid
                    </span>
                  {:else if bill.status === 'Sent'}
                    <span class="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-blue-100 text-blue-700 border border-blue-200 dark:bg-blue-500/10 dark:text-blue-400 dark:border-blue-500/20">Sent</span>
                  {:else}
                    <span class="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-gray-100 text-gray-600 border border-gray-200 dark:bg-gray-500/10 dark:text-gray-400 dark:border-gray-500/20">{bill.status}</span>
                  {/if}
                </td>
                <td class="py-3 px-4 text-right">
                  <button class="p-1.5 text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white rounded bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors">
                    <Download class="w-4 h-4" />
                  </button>
                </td>
              </tr>
            {/each}
          {/if}
        </tbody>
      </table>
    </div>
  </Card>
</div>
