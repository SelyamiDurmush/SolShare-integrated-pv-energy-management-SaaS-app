<script lang="ts">
  import { onMount } from 'svelte';
  import { ShieldAlert, Users, Building, Plus, X, Pencil } from 'lucide-svelte';
  import Button from '$lib/components/ui/Button.svelte';
  import Card from '$lib/components/ui/Card.svelte';
  
  let activeTab = $state('users');
  let users = $state<any[]>([]);
  let searchQuery = $state('');

  // ── Add User Modal ──────────────────────────────
  let showAddUserModal = $state(false);
  let addError = $state('');
  let isAdding = $state(false);
  let addName = $state('');
  let addEmail = $state('');
  let addPassword = $state('');
  let addRole = $state('resident');

  // ── Edit User Modal ─────────────────────────────
  let showEditUserModal = $state(false);
  let editUser = $state<any | null>(null);
  let editError = $state('');
  let isSaving = $state(false);
  let editName = $state('');
  let editEmail = $state('');
  let editRole = $state('resident');
  let editIsActive = $state(true);
  let editNewPassword = $state('');

  onMount(() => { fetchUsers(); });

  async function fetchUsers() {
    const token = localStorage.getItem('access_token');
    try {
      const res = await fetch('http://127.0.0.1:8000/api/v1/users/', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) users = await res.json();
    } catch (e) { console.error(e); }
  }

  // ── Add User ────────────────────────────────────
  async function handleAddUser(e: Event) {
    e.preventDefault();
    isAdding = true;
    addError = '';
    const token = localStorage.getItem('access_token');
    try {
      const res = await fetch('http://127.0.0.1:8000/api/v1/users/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify({ email: addEmail, password: addPassword, full_name: addName, role: addRole })
      });
      if (res.ok) {
        users = [...users, await res.json()];
        showAddUserModal = false;
        addName = addEmail = addPassword = '';
        addRole = 'resident';
      } else {
        const err = await res.json();
        addError = err.detail || 'Failed to create user.';
      }
    } catch { addError = 'Network error.'; }
    finally { isAdding = false; }
  }

  // ── Open Edit Modal ─────────────────────────────
  function openEditModal(user: any) {
    editUser = user;
    editName = user.full_name || '';
    editEmail = user.email;
    editRole = user.role;
    editIsActive = user.is_active;
    editNewPassword = '';
    editError = '';
    showEditUserModal = true;
  }

  // ── Save Edit ───────────────────────────────────
  async function handleEditUser(e: Event) {
    e.preventDefault();
    isSaving = true;
    editError = '';
    const token = localStorage.getItem('access_token');

    const payload: Record<string, any> = {
      full_name: editName,
      email: editEmail,
      role: editRole,
      is_active: editIsActive
    };
    if (editNewPassword.trim()) payload.password = editNewPassword;

    try {
      const res = await fetch(`http://127.0.0.1:8000/api/v1/users/${editUser.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        const updated = await res.json();
        // Replace in the local array instantly
        users = users.map(u => u.id === updated.id ? updated : u);
        showEditUserModal = false;
        editUser = null;
      } else {
        const err = await res.json();
        editError = err.detail || 'Failed to update user.';
      }
    } catch { editError = 'Network error.'; }
    finally { isSaving = false; }
  }

  let filteredUsers = $derived(
    users.filter(u =>
      u.email.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (u.full_name && u.full_name.toLowerCase().includes(searchQuery.toLowerCase()))
    )
  );

  function formatRole(role: string) {
    return role.split('_').map((w: string) => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
  }

  function getRoleBadgeStyles(role: string) {
    switch (role) {
      case 'admin':         return 'bg-red-100 text-red-700 dark:bg-red-500/10 dark:text-red-400 border-red-200 dark:border-red-500/20';
      case 'property_manager': return 'bg-purple-100 text-purple-700 dark:bg-purple-500/10 dark:text-purple-400 border-purple-200 dark:border-purple-500/20';
      default:              return 'bg-blue-100 text-blue-700 dark:bg-blue-500/10 dark:text-blue-400 border-blue-200 dark:border-blue-500/20';
    }
  }

  const inputClass = "w-full px-3 py-2 bg-gray-50 dark:bg-black border border-gray-200 dark:border-gray-700 text-gray-900 dark:text-gray-100 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 placeholder-gray-400 dark:placeholder-gray-500 transition-colors";
  const selectClass = `${inputClass} appearance-none cursor-pointer`;
</script>

<div class="space-y-6 relative">
  <div class="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-4">
    <div>
      <h1 class="text-3xl font-bold tracking-tight text-gray-900 dark:text-white mb-2 flex items-center transition-colors">
        <ShieldAlert class="w-8 h-8 mr-3 text-red-500" /> Administration
      </h1>
      <p class="text-gray-600 dark:text-gray-400 transition-colors">System-level management. Restricted to admins.</p>
    </div>
    <Button variant="primary" className="flex items-center" onclick={() => showAddUserModal = true}>
      <Plus class="w-4 h-4 mr-2" /> New User
    </Button>
  </div>

  <!-- Tabs -->
  <div class="flex border-b border-gray-200 dark:border-gray-800 transition-colors">
    <button onclick={() => activeTab = 'users'} class={`px-4 py-3 font-medium text-sm flex items-center transition-colors ${activeTab === 'users' ? 'border-b-2 border-blue-500 text-blue-600 dark:text-blue-400' : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'}`}>
      <Users class="w-4 h-4 mr-2" /> Users & Roles
    </button>
    <button onclick={() => activeTab = 'buildings'} class={`px-4 py-3 font-medium text-sm flex items-center transition-colors ${activeTab === 'buildings' ? 'border-b-2 border-blue-500 text-blue-600 dark:text-blue-400' : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'}`}>
      <Building class="w-4 h-4 mr-2" /> Properties
    </button>
  </div>

  {#if activeTab === 'users'}
    <Card>
      <div class="flex justify-between items-center mb-6">
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white">Registered Users</h3>
        <input type="text" bind:value={searchQuery} placeholder="Search name or email..." class="bg-gray-50 dark:bg-black/50 border border-gray-200 dark:border-gray-800 rounded-md px-3 py-1.5 text-sm outline-none focus:ring-2 focus:ring-blue-500 transition-all text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500" />
      </div>
      <div class="overflow-x-auto">
        <table class="w-full text-left border-collapse">
          <thead>
            <tr class="border-b border-gray-200 dark:border-gray-800 text-gray-500 dark:text-gray-400 text-xs uppercase tracking-wider">
              <th class="py-3 px-4 font-medium">Name</th>
              <th class="py-3 px-4 font-medium">Email</th>
              <th class="py-3 px-4 font-medium">Role</th>
              <th class="py-3 px-4 font-medium">Status</th>
              <th class="py-3 px-4 font-medium text-right">Actions</th>
            </tr>
          </thead>
          <tbody class="text-sm divide-y divide-gray-200 dark:divide-gray-800">
            {#each filteredUsers as user}
              <tr class="hover:bg-gray-50 dark:hover:bg-gray-800/30 transition-colors">
                <td class="py-3 px-4 font-medium text-gray-900 dark:text-white">{user.full_name || '—'}</td>
                <td class="py-3 px-4 text-gray-600 dark:text-gray-400">{user.email}</td>
                <td class="py-3 px-4">
                  <span class={`px-2 py-1 rounded-full text-xs font-semibold border ${getRoleBadgeStyles(user.role)}`}>
                    {formatRole(user.role)}
                  </span>
                </td>
                <td class="py-3 px-4">
                  <span class={`px-2 py-1 rounded-full text-xs font-semibold ${user.is_active ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-400' : 'bg-gray-100 text-gray-500 dark:bg-gray-800 dark:text-gray-400'}`}>
                    {user.is_active ? 'Active' : 'Inactive'}
                  </span>
                </td>
                <td class="py-3 px-4 text-right">
                  <button onclick={() => openEditModal(user)} class="inline-flex items-center gap-1.5 text-blue-500 hover:text-blue-700 dark:hover:text-blue-300 font-medium text-sm transition-colors hover:bg-blue-50 dark:hover:bg-blue-500/10 px-2 py-1 rounded-md">
                    <Pencil class="w-3.5 h-3.5" /> Edit
                  </button>
                </td>
              </tr>
            {:else}
              <tr>
                <td colspan="5" class="py-10 text-center text-gray-500 dark:text-gray-400">No users found matching your search.</td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    </Card>
  {:else if activeTab === 'buildings'}
    <Card>
      <p class="text-gray-500 dark:text-gray-400 py-10 text-center">In development — manage buildings and apartments.</p>
    </Card>
  {/if}
</div>

<!-- ══ ADD USER MODAL ══════════════════════════════════════════════ -->
{#if showAddUserModal}
  <div class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-gray-900/50 dark:bg-black/60 backdrop-blur-sm">
    <div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl shadow-2xl w-full max-w-md overflow-hidden">
      <div class="flex justify-between items-center p-5 border-b border-gray-100 dark:border-gray-800/60">
        <h2 class="text-xl font-bold text-gray-900 dark:text-white">Create New User</h2>
        <button onclick={() => showAddUserModal = false} class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 p-1 rounded-md hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors">
          <X class="w-5 h-5" />
        </button>
      </div>
      <form onsubmit={handleAddUser} class="p-6 space-y-4">
        {#if addError}
          <div class="p-3 bg-red-50 text-red-600 dark:bg-red-500/10 dark:text-red-400 border border-red-200 dark:border-red-500/20 rounded-lg text-sm">{addError}</div>
        {/if}
        <div>
          <label for="add-name" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Full Name</label>
          <input type="text" id="add-name" bind:value={addName} required class={inputClass} placeholder="Jane Doe" />
        </div>
        <div>
          <label for="add-email" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Email Address</label>
          <input type="email" id="add-email" bind:value={addEmail} required class={inputClass} placeholder="jane@solshare.com" />
        </div>
        <div>
          <label for="add-password" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Temporary Password</label>
          <input type="password" id="add-password" bind:value={addPassword} required minlength="6" class={inputClass} placeholder="••••••••" />
        </div>
        <div>
          <label for="add-role" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">System Role</label>
          <select id="add-role" bind:value={addRole} class={selectClass}>
            <option value="resident">Resident</option>
            <option value="property_manager">Property Manager</option>
            <option value="admin">System Administrator</option>
          </select>
        </div>
        <div class="pt-4 flex justify-end gap-3 border-t border-gray-100 dark:border-gray-800/60">
          <button type="button" onclick={() => showAddUserModal = false} class="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors">Cancel</button>
          <button type="submit" disabled={isAdding} class="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 rounded-lg transition-colors shadow-sm">
            {isAdding ? 'Creating...' : 'Create User'}
          </button>
        </div>
      </form>
    </div>
  </div>
{/if}

<!-- ══ EDIT USER MODAL ═════════════════════════════════════════════ -->
{#if showEditUserModal && editUser}
  <div class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-gray-900/50 dark:bg-black/60 backdrop-blur-sm">
    <div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl shadow-2xl w-full max-w-md overflow-hidden">
      <div class="flex justify-between items-center p-5 border-b border-gray-100 dark:border-gray-800/60">
        <div>
          <h2 class="text-xl font-bold text-gray-900 dark:text-white">Edit User</h2>
          <p class="text-xs text-gray-400 mt-0.5">ID #{editUser.id}</p>
        </div>
        <button onclick={() => showEditUserModal = false} class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 p-1 rounded-md hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors">
          <X class="w-5 h-5" />
        </button>
      </div>
      <form onsubmit={handleEditUser} class="p-6 space-y-4">
        {#if editError}
          <div class="p-3 bg-red-50 text-red-600 dark:bg-red-500/10 dark:text-red-400 border border-red-200 dark:border-red-500/20 rounded-lg text-sm">{editError}</div>
        {/if}
        <div>
          <label for="edit-name" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Full Name</label>
          <input type="text" id="edit-name" bind:value={editName} required class={inputClass} />
        </div>
        <div>
          <label for="edit-email" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Email Address</label>
          <input type="email" id="edit-email" bind:value={editEmail} required class={inputClass} />
        </div>
        <div>
          <label for="edit-role" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">System Role</label>
          <select id="edit-role" bind:value={editRole} class={selectClass}>
            <option value="resident">Resident</option>
            <option value="property_manager">Property Manager</option>
            <option value="admin">System Administrator</option>
          </select>
        </div>
        <div>
          <label for="edit-status" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Account Status</label>
          <select id="edit-status" bind:value={editIsActive} class={selectClass}>
            <option value={true}>Active</option>
            <option value={false}>Inactive (Suspended)</option>
          </select>
        </div>
        <div>
          <label for="edit-password" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            New Password <span class="text-gray-400 font-normal">(leave blank to keep current)</span>
          </label>
          <input type="password" id="edit-password" bind:value={editNewPassword} minlength="6" class={inputClass} placeholder="••••••••" />
        </div>
        <div class="pt-4 flex justify-end gap-3 border-t border-gray-100 dark:border-gray-800/60">
          <button type="button" onclick={() => showEditUserModal = false} class="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors">Cancel</button>
          <button type="submit" disabled={isSaving} class="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 rounded-lg transition-colors shadow-sm flex items-center gap-2">
            {#if isSaving}
              <span class="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></span> Saving...
            {:else}
              Save Changes
            {/if}
          </button>
        </div>
      </form>
    </div>
  </div>
{/if}
