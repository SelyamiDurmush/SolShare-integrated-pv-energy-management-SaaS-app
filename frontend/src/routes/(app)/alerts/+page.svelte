<script lang="ts">
  import { onMount } from 'svelte';
  import { Bell, AlertTriangle, Info, CheckCircle, Check, CheckCheck, Trash2 } from 'lucide-svelte';
  import Card from '$lib/components/ui/Card.svelte';
  import { alertState } from '$lib/user.svelte';

  interface AlertItem {
    id: number;
    severity: 'critical' | 'warning' | 'info' | 'positive';
    category: string;
    title: string;
    message: string;
    is_read: boolean;
    is_resolved: boolean;
    created_at: string;
    building_id: number | null;
    apartment_id: number | null;
  }

  let alerts = $state<AlertItem[]>([]);
  let isLoading = $state(true);
  let showResolved = $state(false);
  let removing = $state<Set<number>>(new Set());
  let isBulkWorking = $state(false);

  function token() { return localStorage.getItem('access_token') ?? ''; }

  async function loadAlerts() {
    isLoading = true;
    try {
      const res = await fetch(
        `http://127.0.0.1:8000/api/v1/alerts/?include_resolved=${showResolved}`,
        { headers: { Authorization: `Bearer ${token()}` } }
      );
      if (res.ok) alerts = await res.json();
    } finally { isLoading = false; }
  }

  async function markRead(id: number) {
    await fetch(`http://127.0.0.1:8000/api/v1/alerts/${id}/read`, {
      method: 'PATCH', headers: { Authorization: `Bearer ${token()}` }
    });
    alerts = alerts.map(a => a.id === id ? { ...a, is_read: true } : a);
    await alertState.refresh();
  }

  async function resolve(id: number) {
    removing = new Set([...removing, id]);
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/v1/alerts/${id}/resolve`, {
        method: 'PATCH', headers: { Authorization: `Bearer ${token()}` }
      });
      if (res.ok) {
        // Small delay so the animation plays
        await new Promise(r => setTimeout(r, 250));
        alerts = alerts.filter(a => a.id !== id);
        await alertState.refresh();
      }
    } finally {
      removing.delete(id);
      removing = new Set(removing);
    }
  }

  async function markAllRead() {
    isBulkWorking = true;
    try {
      const unread = alerts.filter(a => !a.is_read);
      await Promise.all(unread.map(a =>
        fetch(`http://127.0.0.1:8000/api/v1/alerts/${a.id}/read`, {
          method: 'PATCH', headers: { Authorization: `Bearer ${token()}` }
        })
      ));
      alerts = alerts.map(a => ({ ...a, is_read: true }));
      await alertState.refresh();
    } finally { isBulkWorking = false; }
  }

  async function resolveAll() {
    isBulkWorking = true;
    try {
      const active = alerts.filter(a => !a.is_resolved);
      for (const a of active) {
        removing = new Set([...removing, a.id]);
      }
      await Promise.all(active.map(a =>
        fetch(`http://127.0.0.1:8000/api/v1/alerts/${a.id}/resolve`, {
          method: 'PATCH', headers: { Authorization: `Bearer ${token()}` }
        })
      ));
      await new Promise(r => setTimeout(r, 300));
      alerts = [];
      removing = new Set();
      await alertState.refresh();
    } finally { isBulkWorking = false; }
  }

  onMount(loadAlerts);

  const SEV = {
    critical: { bg: 'bg-red-50 dark:bg-red-500/10', border: 'border-red-200 dark:border-red-500/20',
                badge: 'bg-red-100 dark:bg-red-500/20 text-red-700 dark:text-red-400', iconColor: 'text-red-500' },
    warning:  { bg: 'bg-amber-50 dark:bg-amber-500/10', border: 'border-amber-200 dark:border-amber-500/20',
                badge: 'bg-amber-100 dark:bg-amber-500/20 text-amber-700 dark:text-amber-400', iconColor: 'text-amber-500' },
    info:     { bg: 'bg-blue-50 dark:bg-blue-500/10', border: 'border-blue-200 dark:border-blue-500/20',
                badge: 'bg-blue-100 dark:bg-blue-500/20 text-blue-700 dark:text-blue-400', iconColor: 'text-blue-500' },
    positive: { bg: 'bg-emerald-50 dark:bg-emerald-500/10', border: 'border-emerald-200 dark:border-emerald-500/20',
                badge: 'bg-emerald-100 dark:bg-emerald-500/20 text-emerald-700 dark:text-emerald-400', iconColor: 'text-emerald-500' },
  };

  function fmt(iso: string) {
    return new Date(iso).toLocaleString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
  }

  let unreadCount = $derived(alerts.filter(a => !a.is_read).length);
  let activeCount = $derived(alerts.filter(a => !a.is_resolved).length);
</script>

<div class="space-y-5">
  <!-- ── Header ────────────────────────────────────────────── -->
  <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
    <div class="flex items-center gap-3">
      <div class="p-2.5 rounded-xl {activeCount > 0 ? 'bg-red-100 dark:bg-red-500/20' : 'bg-emerald-100 dark:bg-emerald-500/20'}">
        <Bell class="w-6 h-6 {activeCount > 0 ? 'text-red-600 dark:text-red-400' : 'text-emerald-600 dark:text-emerald-400'}" />
      </div>
      <div>
        <h1 class="text-3xl font-bold tracking-tight text-gray-900 dark:text-white">System Alerts</h1>
        <p class="text-sm text-gray-500 dark:text-gray-400">
          {#if unreadCount > 0}
            <span class="text-red-500 font-semibold">{unreadCount} unread</span>
            {#if activeCount !== unreadCount} · {activeCount} total active{/if}
          {:else if activeCount > 0}
            {activeCount} active alerts · all read
          {:else}
            All clear — no active alerts
          {/if}
        </p>
      </div>
    </div>

    <!-- Controls -->
    <div class="flex flex-wrap items-center gap-2">
      <label class="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400 cursor-pointer select-none px-2">
        <input type="checkbox" bind:checked={showResolved} onchange={loadAlerts} class="rounded accent-blue-500" />
        Show resolved
      </label>

      {#if unreadCount > 0}
        <button
          onclick={markAllRead}
          disabled={isBulkWorking}
          class="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-blue-700 dark:text-blue-400 bg-blue-50 dark:bg-blue-500/10 border border-blue-200 dark:border-blue-500/20 rounded-lg hover:bg-blue-100 dark:hover:bg-blue-500/20 transition-colors disabled:opacity-50"
        >
          <CheckCheck class="w-3.5 h-3.5" /> Mark all read
        </button>
      {/if}

      {#if activeCount > 1}
        <button
          onclick={resolveAll}
          disabled={isBulkWorking}
          class="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-emerald-700 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-500/10 border border-emerald-200 dark:border-emerald-500/20 rounded-lg hover:bg-emerald-100 dark:hover:bg-emerald-500/20 transition-colors disabled:opacity-50"
        >
          {#if isBulkWorking}
            <span class="w-3.5 h-3.5 border-2 border-current/30 border-t-current rounded-full animate-spin"></span>
          {:else}
            <Trash2 class="w-3.5 h-3.5" />
          {/if}
          Resolve all
        </button>
      {/if}

      <button
        onclick={loadAlerts}
        class="px-3 py-1.5 text-xs font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
      >
        Refresh
      </button>
    </div>
  </div>

  <!-- ── Alert List ─────────────────────────────────────────── -->
  {#if isLoading}
    <div class="space-y-3">
      {#each [1,2,3] as _}
        <div class="h-20 bg-gray-100 dark:bg-gray-800/50 rounded-xl animate-pulse border border-gray-200 dark:border-gray-800"></div>
      {/each}
    </div>

  {:else if alerts.length === 0}
    <Card>
      <div class="text-center py-16">
        <div class="w-20 h-20 bg-emerald-100 dark:bg-emerald-500/20 rounded-full flex items-center justify-center mx-auto mb-5 ring-4 ring-emerald-100 dark:ring-emerald-500/10">
          <CheckCircle class="w-10 h-10 text-emerald-500" />
        </div>
        <h3 class="text-xl font-bold text-gray-900 dark:text-white mb-2">All Clear! 🎉</h3>
        <p class="text-gray-500 dark:text-gray-400 max-w-sm mx-auto">
          {showResolved ? 'No alerts match your filters.' : 'No active alerts. The system is running normally.'}
        </p>
      </div>
    </Card>

  {:else}
    <div class="space-y-2.5">
      {#each alerts as alert (alert.id)}
        {@const cfg = SEV[alert.severity]}
        {@const isRemoving = removing.has(alert.id)}
        <div
          class={`relative border rounded-xl p-4 cursor-pointer transition-all duration-300 ${cfg.bg} ${cfg.border}
            ${isRemoving ? 'opacity-0 scale-95 -translate-x-4' : ''}
            ${!alert.is_read ? 'shadow-sm' : 'opacity-80'}
          `}
          role="button"
          tabindex="0"
          onclick={() => !alert.is_read && markRead(alert.id)}
          onkeydown={(e) => e.key === 'Enter' && !alert.is_read && markRead(alert.id)}
        >
          <!-- Unread dot -->
          {#if !alert.is_read}
            <span class="absolute top-4 right-[52px] w-2 h-2 bg-red-500 rounded-full animate-pulse"></span>
          {/if}

          <div class="flex items-start gap-3">
            <!-- Severity icon -->
            <div class="shrink-0 mt-0.5">
              {#if alert.severity === 'critical' || alert.severity === 'warning'}
                <AlertTriangle class={`w-5 h-5 ${cfg.iconColor}`} />
              {:else if alert.severity === 'positive'}
                <CheckCircle class={`w-5 h-5 ${cfg.iconColor}`} />
              {:else}
                <Info class={`w-5 h-5 ${cfg.iconColor}`} />
              {/if}
            </div>

            <!-- Content -->
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2 mb-0.5 flex-wrap">
                <span class={`text-[10px] font-bold uppercase px-2 py-0.5 rounded-full ${cfg.badge}`}>
                  {alert.severity}
                </span>
                <span class="text-[10px] text-gray-400 uppercase tracking-wide">
                  {alert.category.replace(/_/g, ' ')}
                </span>
              </div>
              <p class="font-semibold text-gray-900 dark:text-white text-sm">{alert.title}</p>
              <p class="text-sm text-gray-600 dark:text-gray-400 mt-0.5">{alert.message}</p>
              <p class="text-[11px] text-gray-400 mt-2">{fmt(alert.created_at)}</p>
            </div>

            <!-- Resolve button -->
            {#if !alert.is_resolved}
              <button
                onclick={(e) => { e.stopPropagation(); resolve(alert.id); }}
                disabled={isRemoving}
                title="Resolve"
                class="shrink-0 mt-0.5 w-8 h-8 flex items-center justify-center rounded-lg text-gray-400 hover:text-emerald-600 hover:bg-emerald-50 dark:hover:bg-emerald-500/10 transition-all disabled:opacity-50"
              >
                {#if isRemoving}
                  <span class="w-4 h-4 border-2 border-current/30 border-t-emerald-500 rounded-full animate-spin block"></span>
                {:else}
                  <Check class="w-4 h-4" />
                {/if}
              </button>
            {:else}
              <span class="shrink-0 mt-0.5 w-8 h-8 flex items-center justify-center rounded-lg text-emerald-500 bg-emerald-50 dark:bg-emerald-500/10" title="Resolved">
                <CheckCircle class="w-4 h-4" />
              </span>
            {/if}
          </div>
        </div>
      {/each}
    </div>
  {/if}
</div>
