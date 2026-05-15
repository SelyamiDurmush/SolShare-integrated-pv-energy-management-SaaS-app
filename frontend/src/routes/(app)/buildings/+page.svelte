<script lang="ts">
  import { onMount } from "svelte";
  import Card from "$lib/components/ui/Card.svelte";
  import Button from "$lib/components/ui/Button.svelte";
  import {
    Building2,
    Plus,
    MapPin,
    Zap,
    House,
    X,
    Pencil,
    Trash2,
    Power,
    PowerOff,
    Users,
    Settings,
  } from "lucide-svelte";

  import { userState } from "$lib/user.svelte";

  interface Apartment {
    id: number;
    unit_number: string;
    resident_id: number | null;
    resident_name: string | null;
    allocation_method: string;
  }

  interface User {
    id: number;
    email: string;
    full_name: string | null;
    role: string;
  }

  interface Building {
    id: number;
    name: string | null;
    address: string;
    manager_id: number;
    grid_connection_capacity_kw: number | null;
    is_active: boolean;
    apartments: Apartment[];
  }

  let buildings = $state<Building[]>([]);
  let isLoading = $state(true);
  let loadError = $state("");

  // Building Management State
  let showModal = $state(false);
  let isSubmitting = $state(false);
  let formError = $state("");
  let formName = $state("");
  let formAddress = $state("");
  let formCapacity = $state("");
  let editingBuildingId = $state<number | null>(null);

  // Unit Management State
  let showUnitModal = $state(false);
  let selectedBuilding = $state<Building | null>(null);
  let residents = $state<User[]>([]);
  let unitFormNumber = $state("");
  let unitFormResidentName = $state("");
  let isManagingUnits = $state(false);

  function openAddModal() {
    editingBuildingId = null;
    formName = formAddress = formCapacity = "";
    formError = "";
    showModal = true;
  }

  function openEditModal(b: Building) {
    editingBuildingId = b.id;
    formName = b.name || "";
    formAddress = b.address || "";
    formCapacity = b.grid_connection_capacity_kw?.toString() || "";
    formError = "";
    showModal = true;
  }

  async function openManageUnits(building: Building) {
    selectedBuilding = building;
    showUnitModal = true;
    if (residents.length === 0) {
      await fetchResidents();
    }
  }

  async function fetchResidents() {
    const token = localStorage.getItem("access_token");
    try {
      const res = await fetch("/api/v1/users", {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        residents = await res.json();
      }
    } catch (e) {
      console.error("Failed to fetch residents", e);
    }
  }

  const inputClass =
    "w-full px-3 py-2 bg-gray-50 dark:bg-black border border-gray-200 dark:border-gray-700 text-gray-900 dark:text-gray-100 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 placeholder-gray-400 dark:placeholder-gray-500 transition-colors";

  onMount(() => {
    fetchBuildings();
  });

  async function fetchBuildings() {
    isLoading = true;
    loadError = "";
    const token = localStorage.getItem("access_token");
    try {
      const res = await fetch("/api/v1/buildings", {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        buildings = Array.isArray(data) ? data : [];
      } else {
        loadError = "Failed to load buildings.";
      }
    } catch {
      loadError = "Network error — could not reach backend.";
    } finally {
      isLoading = false;
    }
  }

  async function handleAddBuilding(e: Event) {
    e.preventDefault();
    isSubmitting = true;
    formError = "";
    const token = localStorage.getItem("access_token");
    try {
      const method = editingBuildingId ? "PATCH" : "POST";
      const url = editingBuildingId
        ? `/api/v1/buildings/${editingBuildingId}`
        : "/api/v1/buildings";

      const payload: any = {
        name: formName,
        address: formAddress,
        grid_connection_capacity_kw: parseFloat(formCapacity),
      };

      const res = await fetch(url, {
        method,
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(payload),
      });
      if (res.ok) {
        if (editingBuildingId) {
          await fetchBuildings();
        } else {
          const newBuilding = await res.json();
          buildings = [...buildings, newBuilding];
        }
        showModal = false;
        formName = formAddress = formCapacity = "";
        editingBuildingId = null;
      } else {
        const err = await res.json();
        formError = err.detail || "Failed to save building.";
      }
    } catch {
      formError = "Network error.";
    } finally {
      isSubmitting = false;
    }
  }

  async function handleDelete(id: number, e: Event) {
    e.stopPropagation();
    if (
      !confirm(
        "Are you sure you want to delete this building? This action cannot be undone.",
      )
    )
      return;
    const token = localStorage.getItem("access_token");
    try {
      const res = await fetch(`/api/v1/buildings/${id}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        buildings = buildings.filter((b) => b.id !== id);
      } else {
        alert("Failed to delete building");
      }
    } catch {
      alert("Network error.");
    }
  }

  async function handleToggleActive(building: Building, e: Event) {
    e.stopPropagation();
    const token = localStorage.getItem("access_token");
    try {
      const res = await fetch(`/api/v1/buildings/${building.id}`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ is_active: !building.is_active }),
      });
      if (res.ok) {
        building.is_active = !building.is_active;
        buildings = [...buildings];
      } else {
        alert("Failed to toggle building status");
      }
    } catch {
      alert("Network error.");
    }
  }

  async function handleAddUnit(e: Event) {
    e.preventDefault();
    if (!selectedBuilding) return;
    isManagingUnits = true;
    const token = localStorage.getItem("access_token");
    try {
      const res = await fetch(
        `/api/v1/buildings/${selectedBuilding.id}/apartments`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            unit_number: unitFormNumber,
            building_id: selectedBuilding.id,
            resident_name: unitFormResidentName || null,
          }),
        },
      );
      if (res.ok) {
        await fetchBuildings();
        // Update local ref
        const updated = buildings.find((b) => b.id === selectedBuilding?.id);
        if (updated) selectedBuilding = updated;
        unitFormNumber = "";
        unitFormResidentName = "";
      }
    } finally {
      isManagingUnits = false;
    }
  }

  async function handleUpdateUnitResident(
    apartmentId: number,
    residentName: string,
  ) {
    if (!selectedBuilding) return;
    const token = localStorage.getItem("access_token");
    try {
      const res = await fetch(
        `/api/v1/buildings/${selectedBuilding.id}/apartments/${apartmentId}`,
        {
          method: "PATCH",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            resident_name: residentName || null,
          }),
        },
      );
      if (res.ok) {
        await fetchBuildings();
        const updated = buildings.find((b) => b.id === selectedBuilding?.id);
        if (updated) selectedBuilding = updated;
      }
    } catch (e) {
      console.error(e);
    }
  }

  async function handleDeleteUnit(apartmentId: number) {
    if (!selectedBuilding) return;
    if (!confirm("Are you sure you want to delete this unit and its resident?")) return;
    
    const token = localStorage.getItem("access_token");
    try {
      const res = await fetch(`/api/v1/buildings/${selectedBuilding.id}/apartments/${apartmentId}`, {
        method: "DELETE",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      if (res.ok) {
        await fetchBuildings();
        const updated = buildings.find(b => b.id === selectedBuilding?.id);
        if (updated) selectedBuilding = updated;
      }
    } catch (e) {
      console.error(e);
    }
  }

  function displayName(b: Building) {
    return b.name || b.address.split(",")[0];
  }
</script>

<div class="space-y-6">
  <div class="flex justify-between items-center">
    <div>
      <h1
        class="text-3xl font-bold tracking-tight text-gray-900 dark:text-white mb-2 transition-colors"
      >
        Buildings
      </h1>
      <p class="text-gray-600 dark:text-gray-400 transition-colors">
        Manage your shared rooftop PV installations.
      </p>
    </div>
    {#if userState.profile?.role !== "resident"}
      <Button
        variant="primary"
        class="flex items-center whitespace-nowrap"
        onclick={openAddModal}
      >
        <Plus class="w-4 h-4 mr-2" /> Add Building
      </Button>
    {/if}
  </div>

  {#if isLoading}
    <!-- Loading skeleton -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {#each [1, 2, 3] as _}
        <div
          class="bg-white dark:bg-gray-900/50 border border-gray-200 dark:border-gray-800 rounded-xl p-6 animate-pulse"
        >
          <div class="flex justify-between mb-4">
            <div
              class="w-12 h-12 bg-gray-200 dark:bg-gray-800 rounded-lg"
            ></div>
            <div
              class="w-16 h-6 bg-gray-200 dark:bg-gray-800 rounded-full"
            ></div>
          </div>
          <div
            class="h-5 bg-gray-200 dark:bg-gray-800 rounded w-3/4 mb-2"
          ></div>
          <div
            class="h-3 bg-gray-200 dark:bg-gray-800 rounded w-1/2 mb-6"
          ></div>
          <div
            class="grid grid-cols-2 gap-4 pt-4 border-t border-gray-200 dark:border-gray-800"
          >
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
      <button
        onclick={fetchBuildings}
        class="mt-4 text-sm text-blue-500 hover:underline">Try again</button
      >
    </div>
  {:else if buildings.length === 0}
    <div
      class="text-center py-20 border-2 border-dashed border-gray-200 dark:border-gray-800 rounded-2xl"
    >
      <Building2 class="w-12 h-12 text-gray-400 mx-auto mb-4" />
      <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-2">
        No Buildings Found
      </h3>
      {#if userState.profile?.role !== "resident"}
        <p class="text-gray-500 dark:text-gray-400 mb-6">
          Add your first building to get started.
        </p>
        <Button variant="primary" onclick={openAddModal} class="flex items-center whitespace-nowrap">
          <Plus class="w-4 h-4 mr-2" /> Add Building
        </Button>
      {:else}
        <p class="text-gray-500 dark:text-gray-400 mb-6">
          You are not currently assigned to any buildings.
        </p>
      {/if}
    </div>
  {:else}
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {#each buildings as building}
        <Card
          class="hover:border-blue-500/50 dark:hover:border-blue-500/50 transition-all group cursor-pointer relative overflow-hidden"
        >
          <div
            class="absolute inset-0 bg-linear-to-br from-blue-600/5 dark:from-blue-600/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none"
          ></div>

          <div class="flex items-start justify-between mb-4 relative">
            <div
              class="p-3 bg-gray-100 dark:bg-gray-800 rounded-lg group-hover:bg-blue-100 dark:group-hover:bg-blue-900/40 transition-colors"
            >
              <Building2 class="text-blue-600 dark:text-blue-400 w-6 h-6" />
            </div>
            <div class="flex items-center gap-2">
              {#if userState.profile?.role !== "resident"}
                <div
                  class="flex items-center gap-1 opacity-100 sm:opacity-0 group-hover:opacity-100 transition-opacity"
                >
                  <button
                    onclick={(e) => {
                      e.stopPropagation();
                      openManageUnits(building);
                    }}
                    class="p-1.5 text-gray-400 hover:text-emerald-500 hover:bg-emerald-50 dark:hover:bg-emerald-500/10 rounded-md transition-colors"
                    title="Manage Units"
                  >
                    <Settings class="w-4 h-4" />
                  </button>
                  <button
                    onclick={(e) => {
                      e.stopPropagation();
                      openEditModal(building);
                    }}
                    class="p-1.5 text-gray-400 hover:text-blue-500 hover:bg-blue-50 dark:hover:bg-blue-500/10 rounded-md transition-colors"
                    title="Edit Building"
                  >
                    <Pencil class="w-4 h-4" />
                  </button>
                  <button
                    onclick={(e) => handleToggleActive(building, e)}
                    class="p-1.5 text-gray-400 hover:text-amber-500 hover:bg-amber-50 dark:hover:bg-amber-500/10 rounded-md transition-colors"
                    title={building.is_active
                      ? "Deactivate Building"
                      : "Activate Building"}
                  >
                    {#if building.is_active}
                      <PowerOff class="w-4 h-4" />
                    {:else}
                      <Power class="w-4 h-4" />
                    {/if}
                  </button>
                  <button
                    onclick={(e) => handleDelete(building.id, e)}
                    class="p-1.5 text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-500/10 rounded-md transition-colors"
                    title="Delete Building"
                  >
                    <Trash2 class="w-4 h-4" />
                  </button>
                </div>
              {/if}
              {#if building.is_active !== false}
                <span
                  class="px-2 py-1 bg-emerald-100 dark:bg-emerald-500/20 text-emerald-700 dark:text-emerald-400 text-xs font-medium rounded border border-emerald-200 dark:border-emerald-500/20"
                >
                  Active
                </span>
              {:else}
                <span
                  class="px-2 py-1 bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-400 text-xs font-medium rounded border border-gray-200 dark:border-gray-700"
                >
                  Inactive
                </span>
              {/if}
            </div>
          </div>

          <h3
            class="text-xl font-bold text-gray-900 dark:text-white mb-1 relative"
          >
            {displayName(building)}
          </h3>
          <a
            href={`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(building.address)}`}
            target="_blank"
            rel="noopener noreferrer"
            class="text-sm text-gray-500 dark:text-gray-400 flex items-center mb-6 relative hover:text-blue-500 dark:hover:text-blue-400 transition-colors group/link"
          >
            <MapPin
              class="w-3 h-3 mr-1 shrink-0 group-hover/link:animate-bounce"
            />
            <span class="hover:underline">{building.address}</span>
          </a>

          <div
            class="grid grid-cols-2 gap-4 border-t border-gray-200 dark:border-gray-800 pt-4 relative"
          >
            <div>
              <p
                class="text-xs text-gray-500 dark:text-gray-500 mb-1 flex items-center"
              >
                <Zap class="w-3 h-3 mr-1" /> Capacity
              </p>
              <p class="text-sm font-semibold text-gray-800 dark:text-gray-200">
                {building.grid_connection_capacity_kw != null
                  ? `${building.grid_connection_capacity_kw} kWp`
                  : "—"}
              </p>
            </div>
            <div>
              <p
                class="text-xs text-gray-500 dark:text-gray-500 mb-1 flex items-center"
              >
                <House class="w-3 h-3 mr-1" /> Units
              </p>
              <p class="text-sm font-semibold text-gray-800 dark:text-gray-200">
                {building.apartments.length} Apartment{building.apartments
                  .length !== 1
                  ? "s"
                  : ""}
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
  <div
    class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-gray-900/50 dark:bg-black/60 backdrop-blur-sm"
  >
    <div
      class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl shadow-2xl w-full max-w-md overflow-hidden"
    >
      <div
        class="flex justify-between items-center p-5 border-b border-gray-100 dark:border-gray-800/60"
      >
        <h2 class="text-xl font-bold text-gray-900 dark:text-white">
          {editingBuildingId ? "Edit Building" : "Add New Building"}
        </h2>
        <button
          onclick={() => (showModal = false)}
          class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 p-1 rounded-md hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
        >
          <X class="w-5 h-5" />
        </button>
      </div>
      <form onsubmit={handleAddBuilding} class="p-6 space-y-4">
        {#if formError}
          <div
            class="p-3 bg-red-50 text-red-600 dark:bg-red-500/10 dark:text-red-400 border border-red-200 dark:border-red-500/20 rounded-lg text-sm"
          >
            {formError}
          </div>
        {/if}
        <div>
          <label
            for="b-name"
            class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
            >Building Name <span class="text-red-400">*</span></label
          >
          <input
            type="text"
            id="b-name"
            bind:value={formName}
            class={inputClass}
            placeholder="e.g. Sunrise Apartments"
            required
          />
        </div>
        <div>
          <label
            for="b-address"
            class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
            >Full Address <span class="text-red-400">*</span></label
          >
          <input
            type="text"
            id="b-address"
            bind:value={formAddress}
            required
            class={inputClass}
            placeholder="Philipsstraße 8, 52068 Aachen, Germany"
          />
        </div>
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label
              for="b-capacity"
              class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
              >Grid Capacity (kWp) <span class="text-red-400">*</span></label
            >
            <input
              type="number"
              id="b-capacity"
              bind:value={formCapacity}
              step="0.1"
              min="0"
              class={inputClass}
              //placeholder="e.g. 50"
              required
            />
          </div>
        </div>
        <div
          class="pt-4 flex justify-end gap-3 border-t border-gray-100 dark:border-gray-800/60"
        >
          <button
            type="button"
            onclick={() => (showModal = false)}
            class="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
            >Cancel</button
          >
          <button
            type="submit"
            disabled={isSubmitting}
            class="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 rounded-lg transition-colors shadow-sm flex items-center gap-2"
          >
            {#if isSubmitting}
              <span
                class="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"
              ></span> Saving...
            {:else}
              Save Building
            {/if}
          </button>
        </div>
      </form>
    </div>
  </div>
{/if}

<!-- ══ MANAGE UNITS MODAL ══════════════════════════════════════════ -->
{#if showUnitModal && selectedBuilding}
  <div
    class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-gray-900/50 dark:bg-black/60 backdrop-blur-sm"
  >
    <div
      class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl shadow-2xl w-full max-w-2xl overflow-hidden"
    >
      <div
        class="flex justify-between items-center p-5 border-b border-gray-100 dark:border-gray-800/60"
      >
        <div>
          <h2 class="text-xl font-bold text-gray-900 dark:text-white">
            Manage Units: {selectedBuilding.name}
          </h2>
          <p class="text-sm text-gray-500">{selectedBuilding.address}</p>
        </div>
        <button
          onclick={() => (showUnitModal = false)}
          class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 p-1 rounded-md hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
        >
          <X class="w-5 h-5" />
        </button>
      </div>

      <div class="p-6">
        <!-- Add Unit Form -->
        <form onsubmit={handleAddUnit} class="flex gap-3 mb-8 items-end">
          <div class="flex-1">
            <label for="u-number" class="block text-xs font-medium text-gray-500 mb-1"
              >Unit Number</label
            >
            <input
              id="u-number"
              bind:value={unitFormNumber}
              placeholder="e.g. 101"
              required
              class={inputClass}
            />
          </div>
          <div class="flex-1">
            <label for="u-resident" class="block text-xs font-medium text-gray-500 mb-1"
              >Initial Resident (Optional)</label
            >
            <input
              id="u-resident"
              bind:value={unitFormResidentName}
              placeholder="e.g. John Doe"
              class={inputClass}
            />
          </div>
          <Button type="submit" disabled={isManagingUnits} class="flex items-center whitespace-nowrap">
            <Plus class="w-4 h-4 mr-1" /> Add
          </Button>
        </form>

        <!-- Units List -->
        <div class="border rounded-lg overflow-hidden dark:border-gray-800">
          <table class="w-full text-sm">
            <thead class="bg-gray-50 dark:bg-gray-800/50 text-gray-500">
              <tr>
                <th class="px-4 py-2 text-left font-medium">Unit</th>
                <th class="px-4 py-2 text-left font-medium"
                  >Assigned Resident</th
                >
                <th class="px-4 py-2 text-right font-medium w-16">Actions</th>
              </tr>
            </thead>
            <tbody class="divide-y dark:divide-gray-800">
              {#each selectedBuilding.apartments as apt}
                <tr class="dark:text-gray-300 group/row">
                  <td class="px-4 py-3 font-medium">{apt.unit_number}</td>
                  <td class="px-4 py-3">
                    <input
                      type="text"
                      value={apt.resident_name || ""}
                      onblur={(e) =>
                        handleUpdateUnitResident(apt.id, e.currentTarget.value)}
                      placeholder="Enter resident name..."
                      class="bg-transparent border-none focus:ring-0 p-0 text-sm w-full placeholder-gray-400 dark:placeholder-gray-600"
                    />
                  </td>
                  <td class="px-4 py-3 text-right">
                    <button
                      onclick={() => handleDeleteUnit(apt.id)}
                      class="p-1 text-gray-400 hover:text-red-500 opacity-0 group-hover/row:opacity-100 transition-all"
                      title="Delete Unit"
                    >
                      <Trash2 class="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              {/each}
              {#if selectedBuilding.apartments.length === 0}
                <tr>
                  <td colspan="2" class="px-4 py-8 text-center text-gray-400">
                    No units added yet.
                  </td>
                </tr>
              {/if}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
{/if}
