<script lang="ts">
  import { onMount, onDestroy, tick } from 'svelte';
  import { Battery, Sun, Zap, Home, BarChart3, Users, Bell, AlertTriangle, Info, CheckCircle } from 'lucide-svelte';
  import Card from '$lib/components/ui/Card.svelte';
  import { Chart, registerables } from 'chart.js';

  Chart.register(...registerables);

  // ── State ──────────────────────────────────────────────────
  type Period = 'daily' | 'weekly' | 'monthly';
  let activePeriod = $state<Period>('weekly');

  interface EnergyBucket { label: string; production: number; consumption: number; }
  interface AptUsage {
    unit_number: string;
    resident_name: string | null;
    consumption_kwh: number;
    solar_share_kwh: number;
    allocation_method: string;
    building_name: string;
  }

  let energyData = $state<EnergyBucket[]>([]);
  let aptData = $state<AptUsage[]>([]);
  let recentAlerts = $state<any[]>([]);
  let isLoadingChart = $state(true);
  let isLoadingApt = $state(true);

  // Summary KPIs (computed from data)
  let totalProduction = $derived(energyData.reduce((s, d) => s + d.production, 0));
  let totalConsumption = $derived(energyData.reduce((s, d) => s + d.consumption, 0));
  let selfSufficiency = $derived(
    totalConsumption > 0 ? Math.min(100, Math.round((totalProduction / totalConsumption) * 100)) : 0
  );

  // ── Chart instance ─────────────────────────────────────────
  let chartCanvas = $state<HTMLCanvasElement | null>(null);
  let chartInstance: Chart | null = null;

  function destroyChart() {
    if (chartInstance) { chartInstance.destroy(); chartInstance = null; }
  }

  function buildChart(data: EnergyBucket[], dark: boolean) {
    destroyChart();
    const labels = data.map(d => d.label);
    const production = data.map(d => d.production);
    const consumption = data.map(d => d.consumption);

    const gridColor = dark ? 'rgba(255,255,255,0.07)' : 'rgba(0,0,0,0.06)';
    const textColor = dark ? '#9ca3af' : '#6b7280';

    chartInstance = new Chart(chartCanvas as HTMLCanvasElement, {
      type: 'bar',
      data: {
        labels,
        datasets: [
          {
            label: 'PV Production (kWh)',
            data: production,
            backgroundColor: 'rgba(59,130,246,0.75)',
            borderColor: 'rgba(59,130,246,1)',
            borderWidth: 1,
            borderRadius: 4,
          },
          {
            label: 'Consumption (kWh)',
            data: consumption,
            backgroundColor: 'rgba(16,185,129,0.65)',
            borderColor: 'rgba(16,185,129,1)',
            borderWidth: 1,
            borderRadius: 4,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: 'index', intersect: false },
        plugins: {
          legend: { 
            position: 'bottom', 
            labels: { color: textColor, padding: 20, boxWidth: 12, font: { size: 12 } } 
          },
          tooltip: {
            backgroundColor: dark ? '#1f2937' : '#ffffff',
            titleColor: dark ? '#f3f4f6' : '#111827',
            bodyColor: dark ? '#d1d5db' : '#374151',
            borderColor: dark ? '#374151' : '#e5e7eb',
            borderWidth: 1,
            callbacks: {
              label: (ctx) => ` ${ctx.dataset.label}: ${(ctx.parsed?.y ?? 0).toFixed(1)} kWh`
            }
          },
        },
        scales: {
          x: {
            grid: { color: gridColor },
            ticks: { color: textColor, maxRotation: 45, font: { size: 11 } },
          },
          y: {
            grid: { color: gridColor },
            ticks: { 
              color: textColor, 
              font: { size: 11 },
              callback: (v) => `${v} kWh`
            },
          },
        },
      },
    });
  }

  // ── API helpers ────────────────────────────────────────────
  function token() { return localStorage.getItem('access_token') ?? ''; }

  async function loadEnergy(period: Period) {
    isLoadingChart = true;
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/v1/analytics/energy-overview?period=${period}`, {
        headers: { Authorization: `Bearer ${token()}` }
      });
      if (res.ok) {
        const json = await res.json();
        energyData = json.data;
        isLoadingChart = false; // Must be false before tick() to render the canvas element

        await tick();
        if (chartCanvas) {
          const dark = document.documentElement.classList.contains('dark');
          buildChart(energyData, dark);
        }
      } else {
        isLoadingChart = false;
      }
    } catch {
      isLoadingChart = false;
    }
  }

  async function loadApartments() {
    isLoadingApt = true;
    try {
      const res = await fetch('http://127.0.0.1:8000/api/v1/analytics/apartment-usage', {
        headers: { Authorization: `Bearer ${token()}` }
      });
      if (res.ok) aptData = await res.json();
    } finally {
      isLoadingApt = false;
    }
  }

  async function switchPeriod(p: Period) {
    activePeriod = p;
    await loadEnergy(p);
  }

  async function loadAlerts() {
    try {
      const res = await fetch('http://127.0.0.1:8000/api/v1/alerts/?include_resolved=false', {
        headers: { Authorization: `Bearer ${token()}` }
      });
      if (res.ok) recentAlerts = (await res.json()).slice(0, 5);
    } catch { /* silent */ }
  }

  onMount(() => {
    loadEnergy(activePeriod);
    loadApartments();
    loadAlerts();
  });

  onDestroy(destroyChart);
</script>

<div class="space-y-6">

  <!-- ── Page Header ──────────────────────────────────────── -->
  <div>
    <h1 class="text-3xl font-bold tracking-tight text-gray-900 dark:text-white mb-1">Dashboard</h1>
    <p class="text-gray-500 dark:text-gray-400">Energy overview for your SolShare portfolio.</p>
  </div>

  <!-- ── KPI Cards ───────────────────────────────────────── -->
  <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
    <Card className="flex items-center gap-4 bg-gradient-to-br from-blue-50 to-white dark:from-blue-900/30 dark:to-black">
      <div class="p-3 bg-blue-100 dark:bg-blue-500/20 rounded-xl shrink-0">
        <Sun class="w-5 h-5 text-blue-600 dark:text-blue-400" />
      </div>
      <div>
        <p class="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wide font-medium">PV Production</p>
        <p class="text-xl font-bold text-gray-900 dark:text-white">{totalProduction.toFixed(0)} <span class="text-xs text-gray-500">kWh</span></p>
        <p class="text-[10px] text-gray-400">{activePeriod} total</p>
      </div>
    </Card>

    <Card className="flex items-center gap-4 bg-gradient-to-br from-emerald-50 to-white dark:from-emerald-900/30 dark:to-black">
      <div class="p-3 bg-emerald-100 dark:bg-emerald-500/20 rounded-xl shrink-0">
        <Zap class="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
      </div>
      <div>
        <p class="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wide font-medium">Consumption</p>
        <p class="text-xl font-bold text-gray-900 dark:text-white">{totalConsumption.toFixed(0)} <span class="text-xs text-gray-500">kWh</span></p>
        <p class="text-[10px] text-gray-400">{activePeriod} total</p>
      </div>
    </Card>

    <Card className="flex items-center gap-4 bg-gradient-to-br from-purple-50 to-white dark:from-purple-900/30 dark:to-black">
      <div class="p-3 bg-purple-100 dark:bg-purple-500/20 rounded-xl shrink-0">
        <Battery class="w-5 h-5 text-purple-600 dark:text-purple-400" />
      </div>
      <div>
        <p class="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wide font-medium">Self-Sufficiency</p>
        <p class="text-xl font-bold text-gray-900 dark:text-white">{selfSufficiency}%</p>
        <div class="w-16 h-1.5 bg-gray-200 dark:bg-gray-700 rounded-full mt-1">
          <div class="h-full bg-purple-500 rounded-full transition-all" style="width: {selfSufficiency}%"></div>
        </div>
      </div>
    </Card>

    <Card className="flex items-center gap-4 bg-gradient-to-br from-amber-50 to-white dark:from-amber-900/30 dark:to-black">
      <div class="p-3 bg-amber-100 dark:bg-amber-500/20 rounded-xl shrink-0">
        <Home class="w-5 h-5 text-amber-600 dark:text-amber-400" />
      </div>
      <div>
        <p class="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wide font-medium">Apartments</p>
        <p class="text-xl font-bold text-gray-900 dark:text-white">{aptData.length} <span class="text-xs text-gray-500">units</span></p>
        <p class="text-[10px] text-gray-400">monitored</p>
      </div>
    </Card>
  </div>

  <!-- ── Energy Overview Chart ───────────────────────────── -->
  <Card>
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-5">
      <div class="flex items-center gap-2">
        <BarChart3 class="w-5 h-5 text-blue-500" />
        <h2 class="text-lg font-bold text-gray-900 dark:text-white">Energy Overview</h2>
      </div>
      <!-- Period toggle -->
      <div class="flex bg-gray-100 dark:bg-gray-800 rounded-lg p-1 gap-1">
        {#each (['daily', 'weekly', 'monthly'] as Period[]) as period}
          <button
            onclick={() => switchPeriod(period)}
            class={`px-3 py-1.5 text-xs font-semibold rounded-md capitalize transition-all ${
              activePeriod === period
                ? 'bg-white dark:bg-gray-700 text-blue-600 dark:text-blue-400 shadow-sm'
                : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200'
            }`}
          >
            {period}
          </button>
        {/each}
      </div>
    </div>

    {#if isLoadingChart}
      <div class="h-72 flex items-center justify-center">
        <div class="flex flex-col items-center gap-3">
          <span class="w-8 h-8 border-2 border-blue-500/30 border-t-blue-500 rounded-full animate-spin"></span>
          <p class="text-sm text-gray-400">Loading energy data…</p>
        </div>
      </div>
    {:else if energyData.length === 0}
      <div class="h-72 flex items-center justify-center">
        <p class="text-gray-400 text-sm">No meter readings found for this period.</p>
      </div>
    {:else}
      <div class="h-72 relative">
        <canvas bind:this={chartCanvas}></canvas>
      </div>
    {/if}
  </Card>

  <!-- ── Apartment Energy Usage Table ──────────────────────── -->
  <Card>
    <div class="flex items-center gap-2 mb-4">
      <Users class="w-5 h-5 text-emerald-500" />
      <div>
        <h2 class="text-lg font-bold text-gray-900 dark:text-white">Apartment Energy Usage</h2>
        <p class="text-xs text-gray-500 dark:text-gray-400">Last 7 days — sourced from meter readings</p>
      </div>
    </div>

    {#if isLoadingApt}
      <div class="space-y-2">
        {#each [1,2,3,4] as _}
          <div class="h-12 bg-gray-100 dark:bg-gray-800 rounded-lg animate-pulse"></div>
        {/each}
      </div>
    {:else if aptData.length === 0}
      <p class="text-gray-400 text-sm py-8 text-center">No apartment data available.</p>
    {:else}
      <div class="overflow-x-auto -mx-4 sm:mx-0">
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b border-gray-200 dark:border-gray-800">
              <th class="text-left py-3 px-4 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide">Unit</th>
              <th class="text-left py-3 px-4 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide">Resident</th>
              <th class="text-right py-3 px-4 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide">Consumption</th>
              <th class="text-right py-3 px-4 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide">Solar Share</th>
              <th class="text-right py-3 px-4 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide hidden sm:table-cell">Self-Suff.</th>
              <th class="text-center py-3 px-4 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide hidden md:table-cell">Method</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-100 dark:divide-gray-800/60">
            {#each aptData as apt}
              {@const selfSuff = apt.consumption_kwh > 0 ? Math.min(100, Math.round((apt.solar_share_kwh / apt.consumption_kwh) * 100)) : 0}
              <tr class="hover:bg-gray-50 dark:hover:bg-gray-800/40 transition-colors">
                <td class="py-3 px-4 font-bold text-gray-900 dark:text-white">#{apt.unit_number}</td>
                <td class="py-3 px-4 text-gray-600 dark:text-gray-300">
                  {#if apt.resident_name}{apt.resident_name}{:else}<span class="italic text-gray-400">Unassigned</span>{/if}
                </td>
                <td class="py-3 px-4 text-right font-semibold text-gray-900 dark:text-white">
                  {apt.consumption_kwh.toFixed(1)} <span class="text-xs text-gray-500">kWh</span>
                </td>
                <td class="py-3 px-4 text-right">
                  <span class="text-emerald-600 dark:text-emerald-400 font-semibold">{apt.solar_share_kwh.toFixed(1)}</span>
                  <span class="text-xs text-gray-500"> kWh</span>
                </td>
                <td class="py-3 px-4 hidden sm:table-cell">
                  <div class="flex items-center justify-end gap-2">
                    <div class="w-20 h-1.5 bg-gray-200 dark:bg-gray-700 rounded-full">
                      <div class="h-full bg-emerald-500 rounded-full" style="width: {selfSuff}%"></div>
                    </div>
                    <span class="text-xs text-gray-500 w-8 text-right">{selfSuff}%</span>
                  </div>
                </td>
                <td class="py-3 px-4 text-center hidden md:table-cell">
                  <span class="px-2 py-0.5 text-[10px] font-bold rounded-full uppercase
                    {apt.allocation_method === 'dynamic' 
                      ? 'bg-blue-100 dark:bg-blue-500/20 text-blue-700 dark:text-blue-400' 
                      : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400'}">
                    {apt.allocation_method}
                  </span>
                </td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    {/if}
  </Card>

  <!-- ── System Alerts Preview ──────────────────────────── -->
  <Card>
    <div class="flex items-center justify-between mb-4">
      <div class="flex items-center gap-2">
        <Bell class="w-5 h-5 text-red-500" />
        <h2 class="text-lg font-bold text-gray-900 dark:text-white">System Alerts</h2>
        {#if recentAlerts.length > 0}
          <span class="text-xs bg-red-100 dark:bg-red-500/20 text-red-600 dark:text-red-400 px-2 py-0.5 rounded-full font-bold">{recentAlerts.length}</span>
        {/if}
      </div>
      <a href="/alerts" class="text-sm text-blue-500 hover:text-blue-600 hover:underline font-medium">View all →</a>
    </div>

    {#if recentAlerts.length === 0}
      <div class="flex items-center gap-3 py-6 justify-center text-gray-400">
        <CheckCircle class="w-5 h-5 text-emerald-500" />
        <span class="text-sm">No active alerts — system is healthy.</span>
      </div>
    {:else}
      <div class="space-y-2">
        {#each recentAlerts as alert}
          <div class={`flex items-start gap-3 p-3 rounded-lg border ${
            alert.severity === 'critical' ? 'bg-red-50 dark:bg-red-500/10 border-red-200 dark:border-red-500/20' :
            alert.severity === 'warning'  ? 'bg-amber-50 dark:bg-amber-500/10 border-amber-200 dark:border-amber-500/20' :
            'bg-blue-50 dark:bg-blue-500/10 border-blue-200 dark:border-blue-500/20'
          }`}>
            {#if alert.severity === 'critical' || alert.severity === 'warning'}
              <AlertTriangle class={`w-4 h-4 shrink-0 mt-0.5 ${alert.severity === 'critical' ? 'text-red-500' : 'text-amber-500'}`} />
            {:else}
              <Info class="w-4 h-4 shrink-0 mt-0.5 text-blue-500" />
            {/if}
            <div class="flex-1 min-w-0">
              <p class="text-sm font-semibold text-gray-900 dark:text-white">{alert.title}</p>
              <p class="text-xs text-gray-500 dark:text-gray-400 truncate">{alert.message}</p>
            </div>
            {#if !alert.is_read}
              <span class="w-2 h-2 bg-red-500 rounded-full shrink-0 mt-1"></span>
            {/if}
          </div>
        {/each}
      </div>
    {/if}
  </Card>

</div>
