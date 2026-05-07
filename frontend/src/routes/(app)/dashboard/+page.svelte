<script lang="ts">
  import { onMount, onDestroy, tick } from "svelte";
  import {
    Battery,
    Sun,
    Zap,
    House,
    ChartColumn,
    Activity,
    TrendingUp,
    TrendingDown,
    Users,
    Bell,
    TriangleAlert,
    Info,
    CircleCheck,
    Calendar,
    Clock,
  } from "lucide-svelte";
  import Card from "$lib/components/ui/Card.svelte";
  import { Chart, registerables } from "chart.js";

  Chart.register(...registerables);

  // ── State ──────────────────────────────────────────────────
  type Period = "daily" | "weekly" | "monthly";
  let activePeriod = $state<Period>("weekly");

  interface EnergyBucket {
    label: string;
    production: number;
    consumption: number;
  }
  interface AptUsage {
    apartment_id: number;
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
  type BatteryStatusEnum =
    | "charging"
    | "charging_grid"
    | "discharging"
    | "idle"
    | "full"
    | "critically_low"
    | "fault";

  interface BatteryData {
    soc_percentage: number;
    soh_percentage: number;
    power_kw: number;
    estimated_backup_hours: number;
    status_text: string;
    status_enum: BatteryStatusEnum;
    available_kwh: number;
    capacity_kwh: number;
    updated_at: string;
    status?: string; // 'error' sentinel
  }

  let batteryData = $state<BatteryData | null>(null);

  let selectedApartmentId = $state<number | null>(null);

  let filteredAlerts = $derived(
    selectedApartmentId
      ? recentAlerts.filter(
          (a) =>
            a.apartment_id === selectedApartmentId || a.apartment_id === null,
        )
      : recentAlerts,
  );

  let overdueAlertsCount = $derived(
    filteredAlerts.filter((a) => a.severity === "critical").length,
  );
  let pendingAlertsCount = $derived(
    filteredAlerts.filter((a) => a.severity === "warning").length,
  );
  let scheduledAlertsCount = $derived(
    filteredAlerts.filter((a) => a.severity === "info").length,
  );
  let completedAlertsCount = $derived(0);

  let isLoadingChart = $state(true);
  let isLoadingApt = $state(true);
  let isLoadingBattery = $state(true);

  // Summary KPIs (computed from data)
  let totalProduction = $derived(
    energyData.reduce((s, d) => s + d.production, 0),
  );
  let totalConsumption = $derived(
    energyData.reduce((s, d) => s + d.consumption, 0),
  );
  let selfSufficiency = $derived(
    totalConsumption > 0
      ? Math.min(100, Math.round((totalProduction / totalConsumption) * 100))
      : 0,
  );

  // ── Chart instance ─────────────────────────────────────────
  let chartCanvas = $state<HTMLCanvasElement | null>(null);
  let chartInstance: Chart | null = null;

  function destroyChart() {
    if (chartInstance) {
      chartInstance.destroy();
      chartInstance = null;
    }
  }

  function buildChart(data: EnergyBucket[], dark: boolean) {
    destroyChart();
    const labels = data.map((d) => d.label);
    const production = data.map((d) => d.production);
    const consumption = data.map((d) => d.consumption);

    const gridColor = dark ? "rgba(255,255,255,0.07)" : "rgba(0,0,0,0.06)";
    const textColor = dark ? "#9ca3af" : "#6b7280";

    chartInstance = new Chart(chartCanvas as HTMLCanvasElement, {
      type: "bar",
      data: {
        labels,
        datasets: [
          {
            label: "PV Production (kWh)",
            data: production,
            backgroundColor: "rgba(59,130,246,0.75)",
            borderColor: "rgba(59,130,246,1)",
            borderWidth: 1,
            borderRadius: 4,
          },
          {
            label: "Consumption (kWh)",
            data: consumption,
            backgroundColor: "rgba(16,185,129,0.65)",
            borderColor: "rgba(16,185,129,1)",
            borderWidth: 1,
            borderRadius: 4,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: "index", intersect: false },
        plugins: {
          legend: {
            position: "bottom",
            labels: {
              color: textColor,
              padding: 20,
              boxWidth: 12,
              font: { size: 12 },
            },
          },
          tooltip: {
            backgroundColor: dark ? "#1f2937" : "#ffffff",
            titleColor: dark ? "#f3f4f6" : "#111827",
            bodyColor: dark ? "#d1d5db" : "#374151",
            borderColor: dark ? "#374151" : "#e5e7eb",
            borderWidth: 1,
            callbacks: {
              label: (ctx) =>
                ` ${ctx.dataset.label}: ${(ctx.parsed?.y ?? 0).toFixed(1)} kWh`,
            },
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
              callback: (v) => `${v} kWh`,
            },
          },
        },
      },
    });
  }

  // ── API helpers ────────────────────────────────────────────
  function token() {
    return localStorage.getItem("access_token") ?? "";
  }

  async function loadEnergy(period: Period) {
    isLoadingChart = true;
    try {
      const res = await fetch(
        `/api/v1/analytics/energy-overview?period=${period}`,
        {
          headers: { Authorization: `Bearer ${token()}` },
        },
      );
      if (res.ok) {
        const json = await res.json();
        energyData = json.data;
        isLoadingChart = false; // Must be false before tick() to render the canvas element

        await tick();
        if (chartCanvas) {
          const dark = document.documentElement.classList.contains("dark");
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
      const res = await fetch("/api/v1/analytics/apartment-usage", {
        headers: { Authorization: `Bearer ${token()}` },
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
      const res = await fetch("/api/v1/alerts/?include_resolved=false", {
        headers: { Authorization: `Bearer ${token()}` },
      });
      if (res.ok) recentAlerts = (await res.json()).slice(0, 20);
    } catch {
      /* silent */
    }
  }

  async function loadBattery() {
    isLoadingBattery = true;
    try {
      const res = await fetch("/api/v1/analytics/battery-status", {
        headers: { Authorization: `Bearer ${token()}` },
      });
      if (res.ok) batteryData = await res.json();
    } catch {
      /* silent */
    } finally {
      isLoadingBattery = false;
    }
  }

  onMount(() => {
    loadEnergy(activePeriod);
    loadApartments();
    loadAlerts();
    loadBattery();
  });

  onDestroy(destroyChart);
</script>

<div class="space-y-6">
  <!-- ── Page Header ──────────────────────────────────────── -->
  <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
    <div>
      <h1
        class="text-3xl font-bold tracking-tight text-gray-900 dark:text-white mb-1 flex items-center gap-3"
      >
        <div
          class="p-1.5 rounded-lg bg-blue-100 dark:bg-blue-500/20 text-blue-600 dark:text-blue-400"
        >
          <Activity class="w-6 h-6" />
        </div>
        SolShare Core
      </h1>
      <p class="text-gray-500 dark:text-gray-400">
        Smart Energy Management & Trading System
      </p>
    </div>
  </div>

  <!-- ── KPI Cards ───────────────────────────────────────── -->
  <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
    <Card
      class="relative overflow-hidden bg-linear-to-br from-blue-50 to-white dark:from-blue-900/30 dark:to-black transition-all"
    >
      <div class="flex justify-between items-start mb-4">
        <div>
          <p
            class="text-[10px] sm:text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wide font-bold mb-1"
          >
            PV Production
          </p>
          <div class="flex items-baseline gap-1">
            <span
              class="text-2xl sm:text-3xl font-bold text-gray-900 dark:text-white"
              >{totalProduction.toFixed(0)}</span
            >
            <span class="text-sm text-gray-500 font-medium">kWh</span>
          </div>
        </div>
        <div
          class="p-2 sm:p-3 rounded-xl bg-blue-100 dark:bg-blue-500/20 shrink-0"
        >
          <Sun class="w-5 h-5 sm:w-6 sm:h-6 text-blue-600 dark:text-blue-400" />
        </div>
      </div>
      <div
        class="inline-flex items-center gap-1 px-2 py-1 rounded-md bg-blue-100/50 dark:bg-blue-500/10 text-[10px] text-blue-700 dark:text-blue-300 font-medium"
      >
        <TrendingUp class="w-3 h-3" />
        {activePeriod} total
      </div>
    </Card>

    <Card
      class="relative overflow-hidden bg-linear-to-br from-emerald-50 to-white dark:from-emerald-900/30 dark:to-black transition-all"
    >
      <div class="flex justify-between items-start mb-4">
        <div>
          <p
            class="text-[10px] sm:text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wide font-bold mb-1"
          >
            Consumption
          </p>
          <div class="flex items-baseline gap-1">
            <span
              class="text-2xl sm:text-3xl font-bold text-gray-900 dark:text-white"
              >{totalConsumption.toFixed(0)}</span
            >
            <span class="text-sm text-gray-500 font-medium">kWh</span>
          </div>
        </div>
        <div
          class="p-2 sm:p-3 rounded-xl bg-emerald-100 dark:bg-emerald-500/20 shrink-0"
        >
          <Zap
            class="w-5 h-5 sm:w-6 sm:h-6 text-emerald-600 dark:text-emerald-400"
          />
        </div>
      </div>
      <div
        class="inline-flex items-center gap-1 px-2 py-1 rounded-md bg-emerald-100/50 dark:bg-emerald-500/10 text-[10px] text-emerald-700 dark:text-emerald-300 font-medium"
      >
        <TrendingDown class="w-3 h-3" />
        {activePeriod} total
      </div>
    </Card>

    <Card
      class="relative overflow-hidden bg-linear-to-br from-purple-50 to-white dark:from-purple-900/30 dark:to-black transition-all"
    >
      <div class="flex justify-between items-start mb-4">
        <div>
          <p
            class="text-[10px] sm:text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wide font-bold mb-1"
          >
            Self-Sufficiency
          </p>
          <div class="flex items-baseline gap-1">
            <span
              class="text-2xl sm:text-3xl font-bold text-gray-900 dark:text-white"
              >{selfSufficiency}%</span
            >
          </div>
        </div>
        <div
          class="p-2 sm:p-3 rounded-xl bg-purple-100 dark:bg-purple-500/20 shrink-0"
        >
          <Battery
            class="w-5 h-5 sm:w-6 sm:h-6 text-purple-600 dark:text-purple-400"
          />
        </div>
      </div>
      <div
        class="w-full h-1.5 bg-gray-200 dark:bg-gray-800 rounded-full overflow-hidden mt-1"
      >
        <div
          class="h-full bg-purple-500 rounded-full transition-all duration-1000"
          style="width: {selfSufficiency}%"
        ></div>
      </div>
    </Card>

    <Card
      class="relative overflow-hidden bg-linear-to-br from-amber-50 to-white dark:from-amber-900/30 dark:to-black transition-all"
    >
      <div class="flex justify-between items-start mb-4">
        <div>
          <p
            class="text-[10px] sm:text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wide font-bold mb-1"
          >
            Apartments
          </p>
          <div class="flex items-baseline gap-1">
            <span
              class="text-2xl sm:text-3xl font-bold text-gray-900 dark:text-white"
              >{aptData.length}</span
            >
            <span class="text-sm text-gray-500 font-medium">units</span>
          </div>
        </div>
        <div
          class="p-2 sm:p-3 rounded-xl bg-amber-100 dark:bg-amber-500/20 shrink-0"
        >
          <House
            class="w-5 h-5 sm:w-6 sm:h-6 text-amber-600 dark:text-amber-400"
          />
        </div>
      </div>
      <div
        class="inline-flex items-center gap-1 px-2 py-1 rounded-md bg-amber-100/50 dark:bg-amber-500/10 text-[10px] text-amber-700 dark:text-amber-300 font-medium"
      >
        <Activity class="w-3 h-3" /> Active monitoring
      </div>
    </Card>
  </div>

  <!-- ── Energy Analytics Chart ───────────────────────────── -->
  <Card>
    <div
      class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-5"
    >
      <div class="flex items-center gap-3">
        <div
          class="p-1.5 rounded-lg bg-linear-to-br from-indigo-500 to-purple-600 shadow-sm"
        >
          <Activity class="w-5 h-5 text-white" />
        </div>
        <h2
          class="text-lg font-bold text-gray-900 dark:text-white tracking-wide"
        >
          Energy Analytics
        </h2>
      </div>
      <!-- Period toggle -->
      <div class="flex bg-gray-100 dark:bg-gray-800 rounded-lg p-1 gap-1">
        {#each ["daily", "weekly", "monthly"] as Period[] as period}
          <button
            onclick={() => switchPeriod(period)}
            class={`px-3 py-1.5 text-xs font-semibold rounded-md capitalize transition-all ${
              activePeriod === period
                ? "bg-white dark:bg-gray-700 text-blue-600 dark:text-blue-400 shadow-sm"
                : "text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200"
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
          <span
            class="w-8 h-8 border-2 border-blue-500/30 border-t-blue-500 rounded-full animate-spin"
          ></span>
          <p class="text-sm text-gray-400">Loading energy data…</p>
        </div>
      </div>
    {:else if energyData.length === 0}
      <div class="h-72 flex items-center justify-center">
        <p class="text-gray-400 text-sm">
          No meter readings found for this period.
        </p>
      </div>
    {:else}
      <div class="h-72 relative">
        <canvas bind:this={chartCanvas}></canvas>
      </div>
    {/if}
  </Card>

  <!-- ── Middle Section: Battery & Alerts ─────────────────────── -->
  <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
    <!-- ── Battery Storage System ────────────────────────────────────── -->
    <Card
      class="flex flex-col relative overflow-hidden bg-linear-to-br from-gray-50 to-white dark:from-gray-900/30 dark:to-black transition-all"
    >
      <div class="flex items-center justify-between mb-6">
        <div class="flex items-center gap-3">
          <div
            class="p-1.5 rounded-lg bg-emerald-100 dark:bg-emerald-500/20 shadow-sm"
          >
            <Battery class="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
          </div>
          <h2
            class="text-lg font-bold text-gray-900 dark:text-white tracking-wide"
          >
            Battery Storage System
          </h2>
        </div>
        {#if batteryData}
          {@const statusCfg = {
            charging: {
              bg: "bg-blue-100/50 dark:bg-blue-500/10 text-blue-700 dark:text-blue-300 border-blue-200 dark:border-blue-800",
              icon: "text-blue-500",
            },
            charging_grid: {
              bg: "bg-violet-100/50 dark:bg-violet-500/10 text-violet-700 dark:text-violet-300 border-violet-200 dark:border-violet-800",
              icon: "text-violet-500",
            },
            discharging: {
              bg: "bg-amber-100/50 dark:bg-amber-500/10 text-amber-700 dark:text-amber-300 border-amber-200 dark:border-amber-800",
              icon: "text-amber-500",
            },
            idle: {
              bg: "bg-gray-100/50 dark:bg-gray-500/10 text-gray-700 dark:text-gray-300 border-gray-200 dark:border-gray-800",
              icon: "text-gray-500",
            },
            full: {
              bg: "bg-emerald-100/50 dark:bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 border-emerald-200 dark:border-emerald-800",
              icon: "text-emerald-500",
            },
            critically_low: {
              bg: "bg-red-100/50 dark:bg-red-500/10 text-red-700 dark:text-red-300 border-red-200 dark:border-red-800",
              icon: "text-red-500",
            },
            fault: {
              bg: "bg-red-200/70 dark:bg-red-700/20 text-red-800 dark:text-red-200 border-red-400 dark:border-red-700",
              icon: "text-red-600",
            },
          }[batteryData.status_enum] ?? {
            bg: "bg-gray-100/50 dark:bg-gray-500/10 text-gray-700 dark:text-gray-300 border-gray-200 dark:border-gray-800",
            icon: "text-gray-500",
          }}
          <div
            class="px-2 py-1 {statusCfg.bg} text-[10px] font-medium rounded-md flex items-center gap-1 border"
          >
            {#if batteryData.status_enum === "charging" || batteryData.status_enum === "charging_grid"}
              <Zap class="w-3 h-3 {statusCfg.icon}" />
            {:else if batteryData.status_enum === "discharging"}
              <Zap class="w-3 h-3 {statusCfg.icon}" />
            {:else if batteryData.status_enum === "full"}
              <Battery class="w-3 h-3 {statusCfg.icon}" />
            {:else if batteryData.status_enum === "critically_low" || batteryData.status_enum === "fault"}
              <TriangleAlert class="w-3 h-3 {statusCfg.icon}" />
            {:else}
              <Activity class="w-3 h-3 {statusCfg.icon}" />
            {/if}
            <span>{batteryData.status_text}</span>
          </div>
        {/if}
      </div>

      {#if isLoadingBattery}
        <div class="flex-1 flex items-center justify-center min-h-[200px]">
          <div
            class="w-8 h-8 border-2 border-emerald-500/30 border-t-emerald-500 rounded-full animate-spin"
          ></div>
        </div>
      {:else if batteryData && batteryData.status !== "error"}
        <div class="space-y-4 flex-1">
          <!-- State of Charge -->
          <div>
            <div class="flex justify-between items-end mb-2">
              <div class="flex items-center gap-2">
                <div
                  class="p-1.5 rounded bg-emerald-100 dark:bg-emerald-500/20"
                >
                  <Zap class="w-3 h-3 text-emerald-600 dark:text-emerald-400" />
                </div>
                <span
                  class="text-[10px] font-bold tracking-widest text-gray-500 dark:text-gray-400 uppercase"
                  >State of Charge (SoC)</span
                >
              </div>
              <div class="text-right">
                <span
                  class="text-2xl font-bold text-gray-900 dark:text-white leading-none"
                  >{batteryData.soc_percentage.toFixed(1)}%</span
                >
                <p
                  class="text-[10px] font-bold text-emerald-500 dark:text-emerald-400 mt-0.5"
                >
                  {batteryData.available_kwh.toFixed(1)} kWh Available
                </p>
              </div>
            </div>
            <div
              class="w-full h-2 bg-gray-200 dark:bg-gray-800 rounded-full overflow-hidden"
            >
              <div
                class="h-full bg-emerald-500 dark:bg-emerald-400 rounded-full transition-all duration-1000"
                style="width: {batteryData.soc_percentage}%"
              ></div>
            </div>
          </div>

          <!-- State of Health -->
          <div>
            <div class="flex justify-between items-end mb-2">
              <div class="flex items-center gap-2">
                <div class="p-1.5 rounded bg-indigo-100 dark:bg-indigo-500/20">
                  <Activity
                    class="w-3 h-3 text-indigo-600 dark:text-indigo-400"
                  />
                </div>
                <span
                  class="text-[10px] font-bold tracking-widest text-gray-500 dark:text-gray-400 uppercase"
                  >State of Health (SoH)</span
                >
              </div>
              <div class="text-right">
                <span
                  class="text-2xl font-bold text-gray-900 dark:text-white leading-none"
                  >{batteryData.soh_percentage.toFixed(1)}%</span
                >
                <p
                  class="text-[10px] font-bold text-indigo-500 dark:text-indigo-400 mt-0.5"
                >
                  {batteryData.soh_percentage > 90
                    ? "Optimal Condition"
                    : "Needs Maintenance"}
                </p>
              </div>
            </div>
            <div
              class="w-full h-2 bg-gray-200 dark:bg-gray-800 rounded-full overflow-hidden"
            >
              <div
                class="h-full bg-indigo-500 dark:bg-indigo-400 rounded-full transition-all duration-1000"
                style="width: {batteryData.soh_percentage}%"
              ></div>
            </div>
          </div>
        </div>

        <!-- Bottom mini cards -->
        <div class="grid grid-cols-2 gap-3 mt-3">
          <div
            class="bg-gray-100 dark:bg-[#1a1c23]/50 rounded-xl p-3 border border-gray-200 dark:border-gray-800/50"
          >
            <div class="flex items-center gap-2 mb-2">
              <div class="p-1 rounded bg-orange-100 dark:bg-orange-500/20">
                <Sun class="w-3 h-3 text-orange-600 dark:text-orange-400" />
              </div>
              <span
                class="text-[10px] font-bold tracking-widest text-gray-500 uppercase"
                >Current Power</span
              >
            </div>
            <div class="text-xl font-bold text-gray-900 dark:text-white">
              {batteryData.power_kw > 0
                ? "+"
                : ""}{batteryData.power_kw.toFixed(1)}
              <span class="text-sm font-medium text-gray-500">kW</span>
            </div>
            <div
              class="text-[10px] text-emerald-500 font-semibold mt-0.5 truncate"
              title={batteryData.status_text}
            >
              {batteryData.status_text}
            </div>
          </div>
          <div
            class="bg-gray-100 dark:bg-[#1a1c23]/50 rounded-xl p-3 border border-gray-200 dark:border-gray-800/50"
          >
            <div class="flex items-center gap-2 mb-2">
              <div class="p-1 rounded bg-purple-100 dark:bg-purple-500/20">
                <Activity
                  class="w-3 h-3 text-purple-600 dark:text-purple-400"
                />
              </div>
              <span
                class="text-[10px] font-bold tracking-widest text-gray-500 uppercase"
                >Est. Backup Time</span
              >
            </div>
            <div class="text-xl font-bold text-gray-900 dark:text-white">
              {batteryData.estimated_backup_hours.toFixed(1)}
              <span class="text-sm font-medium text-gray-500">hrs</span>
            </div>
            <div class="text-[10px] text-purple-500 font-semibold mt-0.5">
              At Current Load
            </div>
          </div>
        </div>
      {:else}
        <div class="flex-1 flex items-center justify-center min-h-[200px]">
          <p class="text-gray-400 text-sm">Battery data unavailable</p>
        </div>
      {/if}
    </Card>

    <!-- ── System Alerts Preview ──────────────────────────── -->
    <Card class="flex flex-col">
      <div class="flex items-center justify-between mb-4">
        <div class="flex items-center gap-2">
          <Bell class="w-5 h-5 text-purple-500" />
          <h2 class="text-lg font-bold text-gray-900 dark:text-white">
            {selectedApartmentId ? "Resident Alerts" : "System Alerts"}
          </h2>
          {#if filteredAlerts.length > 0}
            <span
              class="text-xs bg-purple-100 dark:bg-purple-500/20 text-purple-600 dark:text-purple-400 px-2 py-0.5 rounded-full font-bold"
            >
              {filteredAlerts.length}
            </span>
          {/if}
        </div>
        <a
          href="/alerts"
          class="text-sm text-blue-500 hover:text-blue-600 hover:underline font-medium"
          >View all →</a
        >
      </div>

      <!-- Summary Pills (like the image) -->
      <div class="grid grid-cols-4 gap-2 mb-6">
        <div
          class="bg-gray-50 dark:bg-[#1a1726] rounded-lg p-2 text-center border border-gray-100 dark:border-purple-900/30"
        >
          <div class="text-lg font-bold text-red-400">{overdueAlertsCount}</div>
          <div class="text-[10px] text-gray-500 uppercase font-medium">
            Overdue
          </div>
        </div>
        <div
          class="bg-gray-50 dark:bg-[#1a1726] rounded-lg p-2 text-center border border-gray-100 dark:border-purple-900/30"
        >
          <div class="text-lg font-bold text-amber-400">
            {pendingAlertsCount}
          </div>
          <div class="text-[10px] text-gray-500 uppercase font-medium">
            Pending
          </div>
        </div>
        <div
          class="bg-gray-50 dark:bg-[#1a1726] rounded-lg p-2 text-center border border-gray-100 dark:border-purple-900/30"
        >
          <div class="text-lg font-bold text-blue-400">
            {scheduledAlertsCount}
          </div>
          <div class="text-[10px] text-gray-500 uppercase font-medium">
            Scheduled
          </div>
        </div>
        <div
          class="bg-gray-50 dark:bg-[#1a1726] rounded-lg p-2 text-center border border-gray-100 dark:border-purple-900/30"
        >
          <div class="text-lg font-bold text-emerald-400">
            {completedAlertsCount}
          </div>
          <div class="text-[10px] text-gray-500 uppercase font-medium">
            Completed
          </div>
        </div>
      </div>

      {#if filteredAlerts.length === 0}
        <div
          class="flex-1 flex items-center gap-3 py-6 justify-center text-gray-400"
        >
          <CircleCheck class="w-5 h-5 text-emerald-500" />
          <span class="text-sm">No active alerts for this context.</span>
        </div>
      {:else}
        <div class="space-y-3 flex-1 overflow-y-auto max-h-[400px] pr-2">
          {#each filteredAlerts.slice(0, 5) as alert}
            <div
              class="bg-white dark:bg-[#15131d] p-4 rounded-xl border border-gray-200 dark:border-gray-800/60 shadow-sm relative overflow-hidden"
            >
              <div class="flex items-start justify-between mb-2">
                <div class="flex items-center gap-2">
                  {#if alert.severity === "critical"}
                    <TriangleAlert class="w-4 h-4 text-red-500" />
                  {:else if alert.severity === "warning"}
                    <Clock class="w-4 h-4 text-amber-500" />
                  {:else}
                    <Info class="w-4 h-4 text-blue-500" />
                  {/if}
                  <h3 class="font-bold text-gray-900 dark:text-white text-sm">
                    {alert.title}
                  </h3>

                  <span
                    class="text-[9px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wider
                  {alert.severity === 'critical'
                      ? 'bg-red-500/20 text-red-400'
                      : alert.severity === 'warning'
                        ? 'bg-amber-500/20 text-amber-400'
                        : 'bg-blue-500/20 text-blue-400'}"
                  >
                    {alert.severity === "critical"
                      ? "HIGH"
                      : alert.severity === "warning"
                        ? "MEDIUM"
                        : "LOW"}
                  </span>
                </div>
              </div>

              <p class="text-xs text-gray-600 dark:text-gray-300 mb-3 ml-6">
                {alert.message}
              </p>

              <div class="flex items-center justify-between ml-6 text-[11px]">
                <div class="flex items-center gap-1.5 text-gray-500">
                  <Calendar class="w-3 h-3" />
                  <span
                    >Due: {new Date(
                      alert.created_at,
                    ).toLocaleDateString()}</span
                  >
                </div>
                <span
                  class="font-bold uppercase tracking-wider
                 {alert.severity === 'critical'
                    ? 'text-red-400'
                    : alert.severity === 'warning'
                      ? 'text-amber-400'
                      : 'text-blue-400'}"
                >
                  {alert.severity === "critical"
                    ? "OVERDUE"
                    : alert.severity === "warning"
                      ? "PENDING"
                      : "SCHEDULED"}
                </span>
              </div>
            </div>
          {/each}
        </div>
      {/if}
    </Card>
  </div>

  <!-- ── Apartment Energy Usage Table ──────────────────────── -->
  <Card>
    <div class="flex items-center gap-2 mb-4">
      <Users class="w-5 h-5 text-emerald-500" />
      <div>
        <h2 class="text-lg font-bold text-gray-900 dark:text-white">
          Apartment Energy Usage
        </h2>
        <p class="text-xs text-gray-500 dark:text-gray-400">
          Last 7 days — sourced from meter readings
        </p>
      </div>
    </div>

    {#if isLoadingApt}
      <div class="space-y-2">
        {#each [1, 2, 3, 4] as _}
          <div
            class="h-12 bg-gray-100 dark:bg-gray-800 rounded-lg animate-pulse"
          ></div>
        {/each}
      </div>
    {:else if aptData.length === 0}
      <p class="text-gray-400 text-sm py-8 text-center">
        No apartment data available.
      </p>
    {:else}
      <div class="overflow-x-auto -mx-4 sm:mx-0">
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b border-gray-200 dark:border-gray-800">
              <th
                class="text-left py-3 px-4 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide"
                >Unit</th
              >
              <th
                class="text-left py-3 px-4 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide"
                >Resident</th
              >
              <th
                class="text-right py-3 px-4 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide"
                >Consumption</th
              >
              <th
                class="text-right py-3 px-4 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide"
                >Solar Share</th
              >
              <th
                class="text-right py-3 px-4 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide hidden sm:table-cell"
                >Self-Suff.</th
              >
              <th
                class="text-center py-3 px-4 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide hidden md:table-cell"
                >Method</th
              >
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-100 dark:divide-gray-800/60">
            {#each aptData as apt}
              {@const selfSuff =
                apt.consumption_kwh > 0
                  ? Math.min(
                      100,
                      Math.round(
                        (apt.solar_share_kwh / apt.consumption_kwh) * 100,
                      ),
                    )
                  : 0}
              <tr
                class="hover:bg-gray-50 dark:hover:bg-gray-800/40 transition-colors cursor-pointer {selectedApartmentId ===
                apt.apartment_id
                  ? 'bg-blue-50/50 dark:bg-[#1a1726]/80 border-l-2 border-purple-500'
                  : 'border-l-2 border-transparent'}"
                onclick={() =>
                  (selectedApartmentId =
                    selectedApartmentId === apt.apartment_id
                      ? null
                      : apt.apartment_id)}
              >
                <td class="py-3 px-4 font-bold text-gray-900 dark:text-white"
                  >{apt.unit_number}</td
                >
                <td class="py-3 px-4 text-gray-600 dark:text-gray-300">
                  {#if apt.resident_name}{apt.resident_name}{:else}<span
                      class="italic text-gray-400">Unassigned</span
                    >{/if}
                </td>
                <td
                  class="py-3 px-4 text-right font-semibold text-gray-900 dark:text-white"
                >
                  {apt.consumption_kwh.toFixed(1)}
                  <span class="text-xs text-gray-500">kWh</span>
                </td>
                <td class="py-3 px-4 text-right">
                  <span
                    class="text-emerald-600 dark:text-emerald-400 font-semibold"
                    >{apt.solar_share_kwh.toFixed(1)}</span
                  >
                  <span class="text-xs text-gray-500"> kWh</span>
                </td>
                <td class="py-3 px-4 hidden sm:table-cell">
                  <div class="flex items-center justify-end gap-2">
                    <div
                      class="w-20 h-1.5 bg-gray-200 dark:bg-gray-700 rounded-full"
                    >
                      <div
                        class="h-full bg-emerald-500 rounded-full"
                        style="width: {selfSuff}%"
                      ></div>
                    </div>
                    <span class="text-xs text-gray-500 w-8 text-right"
                      >{selfSuff}%</span
                    >
                  </div>
                </td>
                <td class="py-3 px-4 text-center hidden md:table-cell">
                  <span
                    class="px-2 py-0.5 text-[10px] font-bold rounded-full uppercase
                    {apt.allocation_method === 'dynamic'
                      ? 'bg-blue-100 dark:bg-blue-500/20 text-blue-700 dark:text-blue-400'
                      : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400'}"
                  >
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
</div>
