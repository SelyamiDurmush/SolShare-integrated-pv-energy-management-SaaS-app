<script lang="ts">
  import { onMount } from 'svelte';
  import Card from '$lib/components/ui/Card.svelte';
  import Button from '$lib/components/ui/Button.svelte';
  import { Building2, Plus, MapPin, Zap, Home, X } from 'lucide-svelte';

  import { userState } from '$lib/user.svelte';

  interface Building {
    id: number;
    name: string | null;
    address: string;
    manager_id: number;
    grid_connection_capacity_kw: number | null;
    apartments: { id: number; unit_number: string }[];
  }

  let buildings = $state<Building[]>([]);
  let isLoading = $state(true);
  let loadError = $state('');

  // ── Add Building Modal ───────────────────────────
  let showModal = $state(false);
  let isSubmitting = $state(false);
  let formError = $state('');
  let formName = $state('');
  let formAddress = $state('');
  let formCapacity = $state('');
  let formUnits = $state('');

  const inputClass = "w-full px-3 py-2 bg-gray-50 dark:bg-black border border-gray-200 dark:border-gray-700 text-gray-900 dark:text-gray-100 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 placeholder-gray-400 dark:placeholder-gray-500 transition-colors";

  onMount(() => { fetchBuildings(); });

  async function fetchBuildings() {
    isLoading = true;
    loadError = '';
    const token = localStorage.getItem('access_token');
    try {
      const res = await fetch('http://127.0.0.1:8000/api/v1/buildings/', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        buildings = await res.json();
      } else {
        loadError = 'Failed to load buildings.';
      }
    } catch {
      loadError = 'Network error — could not reach backend.';
    } finally {
      isLoading = false;
    }
  }

  async function handleAddBuilding(e: Event) {
    e.preventDefault();
    isSubmitting = true;
    formError = '';
    const token = localStorage.getItem('access_token');
    try {
      const res = await fetch('http://127.0.0.1:8000/api/v1/buildings/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify({
          name: formName,
          address: formAddress,
          grid_connection_capacity_kw: parseFloat(formCapacity),
          units_count: parseInt(formUnits)
        })
      });
      if (res.ok) {
        const newBuilding = await res.json();
        buildings = [...buildings, newBuilding];
        showModal = false;
        formName = formAddress = formCapacity = formUnits = '';
      } else {
        const err = await res.json();
        formError = err.detail || 'Failed to create building.';
      }
    } catch {
      formError = 'Network error.';
    } finally {
      isSubmitting = false;
    }
  }

  function displayName(b: Building) {
    return b.name || b.address.split(',')[0];
  }
</script>

<div class="space-y-6">
  <div class="flex justify-between items-center">
    <div>
      <h1 class="text-3xl font-bold tracking-tight text-gray-900 dark:text-white mb-2 transition-colors">Buildings</h1>
      <p class="text-gray-600 dark:text-gray-400 transition-colors">Manage your shared rooftop PV installations.</p>
    </div>
    {#if userState.profile?.role !== 'resident'}
      <Button variant="primary" className="flex items-center" onclick={() => showModal = true}>
        <Plus class="w-4 h-4 mr-2" /> Add Building
      </Button>
    {/if}
  </div>

  {#if isLoading}
    <!-- Loading skeleton -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {#each [1,2,3] as _}
        <div class="bg-white dark:bg-gray-900/50 border border-gray-200 dark:border-gray-800 rounded-xl p-6 animate-pulse">
          <div class="flex justify-between mb-4">
            <div class="w-12 h-12 bg-gray-200 dark:bg-gray-800 rounded-lg"></div>
            <div class="w-16 h-6 bg-gray-200 dark:bg-gray-800 rounded-full"></div>
          </div>
          <div class="h-5 bg-gray-200 dark:bg-gray-800 rounded w-3/4 mb-2"></div>
          <div class="h-3 bg-gray-200 dark:bg-gray-800 rounded w-1/2 mb-6"></div>
          <div class="grid grid-cols-2 gap-4 pt-4 border-t border-gray-200 dark:border-gray-800">
            <div class="h-8 bg-gray-200 dark:bg-gray-800 rounded"></div>
            <div class="h-8 bg-gray-200 dark:bg-gray-800 rounded"></div>
          </div>
        </div>
      {/each}
    </div>

  {:else if loadError}
    <div class="text-center py-20">
      <Building2 class="w-12 h-12 text-gray-400 mx-auto mb-4" />
      <p class="text-red-500 dark:text-red-400 font-medium">{loadError}</p>
      <button onclick={fetchBuildings} class="mt-4 text-sm text-blue-500 hover:underline">Try again</button>
    </div>

  {:else if buildings.length === 0}
    <div class="text-center py-20 border-2 border-dashed border-gray-200 dark:border-gray-800 rounded-2xl">
      <Building2 class="w-12 h-12 text-gray-400 mx-auto mb-4" />
      <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-2">No Buildings Found</h3>
      {#if userState.profile?.role !== 'resident'}
        <p class="text-gray-500 dark:text-gray-400 mb-6">Add your first building to get started.</p>
        <Button variant="primary" onclick={() => showModal = true}>
          <Plus class="w-4 h-4 mr-2" /> Add Building
        </Button>
      {:else}
        <p class="text-gray-500 dark:text-gray-400 mb-6">You are not currently assigned to any buildings.</p>
      {/if}
    </div>

  {:else}
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {#each buildings as building}
        <Card className="hover:border-blue-500/50 dark:hover:border-blue-500/50 transition-all group cursor-pointer relative overflow-hidden">
          <div class="absolute inset-0 bg-gradient-to-br from-blue-600/5 dark:from-blue-600/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none"></div>

          <div class="flex items-start justify-between mb-4 relative">
            <div class="p-3 bg-gray-100 dark:bg-gray-800 rounded-lg group-hover:bg-blue-100 dark:group-hover:bg-blue-900/40 transition-colors">
              <Building2 class="text-blue-600 dark:text-blue-400 w-6 h-6" />
            </div>
            <span class="px-2 py-1 bg-emerald-100 dark:bg-emerald-500/20 text-emerald-700 dark:text-emerald-400 text-xs font-medium rounded border border-emerald-200 dark:border-emerald-500/20">
              Active
            </span>
          </div>

          <h3 class="text-xl font-bold text-gray-900 dark:text-white mb-1 relative">{displayName(building)}</h3>
          <a 
            href={`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(building.address)}`}
            target="_blank"
            rel="noopener noreferrer"
            class="text-sm text-gray-500 dark:text-gray-400 flex items-center mb-6 relative hover:text-blue-500 dark:hover:text-blue-400 transition-colors group/link"
          >
            <MapPin class="w-3 h-3 mr-1 shrink-0 group-hover/link:animate-bounce" /> 
            <span class="hover:underline">{building.address}</span>
          </a>

          <div class="grid grid-cols-2 gap-4 border-t border-gray-200 dark:border-gray-800 pt-4 relative">
            <div>
              <p class="text-xs text-gray-500 dark:text-gray-500 mb-1 flex items-center">
                <Zap class="w-3 h-3 mr-1" /> Capacity
              </p>
              <p class="text-sm font-semibold text-gray-800 dark:text-gray-200">
                {building.grid_connection_capacity_kw != null ? `${building.grid_connection_capacity_kw} kWp` : '—'}
              </p>
            </div>
            <div>
              <p class="text-xs text-gray-500 dark:text-gray-500 mb-1 flex items-center">
                <Home class="w-3 h-3 mr-1" /> Units
              </p>
              <p class="text-sm font-semibold text-gray-800 dark:text-gray-200">
                {building.apartments.length} Apt{building.apartments.length !== 1 ? 's' : ''}
              </p>
            </div>
          </div>
        </Card>
      {/each}
    </div>
  {/if}
</div>

<!-- ══ ADD BUILDING MODAL ══════════════════════════════════════════ -->
{#if showModal}
  <div class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-gray-900/50 dark:bg-black/60 backdrop-blur-sm">
    <div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl shadow-2xl w-full max-w-md overflow-hidden">
      <div class="flex justify-between items-center p-5 border-b border-gray-100 dark:border-gray-800/60">
        <h2 class="text-xl font-bold text-gray-900 dark:text-white">Add New Building</h2>
        <button onclick={() => showModal = false} class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 p-1 rounded-md hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors">
          <X class="w-5 h-5" />
        </button>
      </div>
      <form onsubmit={handleAddBuilding} class="p-6 space-y-4">
        {#if formError}
          <div class="p-3 bg-red-50 text-red-600 dark:bg-red-500/10 dark:text-red-400 border border-red-200 dark:border-red-500/20 rounded-lg text-sm">{formError}</div>
        {/if}
        <div>
          <label for="b-name" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Building Name <span class="text-red-400">*</span></label>
          <input type="text" id="b-name" bind:value={formName} class={inputClass} placeholder="e.g. Sunrise Apartments" required />
        </div>
        <div>
          <label for="b-address" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Full Address <span class="text-red-400">*</span></label>
          <input type="text" id="b-address" bind:value={formAddress} required class={inputClass} placeholder="Philipsstraße 8, 52068 Aachen, Germany" />
        </div>
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label for="b-capacity" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Grid Capacity (kWp) <span class="text-red-400">*</span></label>
            <input type="number" id="b-capacity" bind:value={formCapacity} step="0.1" min="0" class={inputClass} placeholder="e.g. 50" required />
          </div>
          <div>
            <label for="b-units" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Apartment Units <span class="text-red-400">*</span></label>
            <input type="number" id="b-units" bind:value={formUnits} min="1" class={inputClass} placeholder="e.g. 10" required />
          </div>
        </div>
        <div class="pt-4 flex justify-end gap-3 border-t border-gray-100 dark:border-gray-800/60">
          <button type="button" onclick={() => showModal = false} class="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors">Cancel</button>
          <button type="submit" disabled={isSubmitting} class="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 rounded-lg transition-colors shadow-sm flex items-center gap-2">
            {#if isSubmitting}
              <span class="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></span> Saving...
            {:else}
              Save Building
            {/if}
          </button>
        </div>
      </form>
    </div>
  </div>
{/if}
