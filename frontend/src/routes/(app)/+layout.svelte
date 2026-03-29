<script lang="ts">
  import { onMount } from 'svelte';
  import { Sun, Moon, LayoutDashboard, Building2, ReceiptText, Settings, LogOut, Shield, Bell } from 'lucide-svelte';
  import { goto } from '$app/navigation';
  import { userState, alertState } from '$lib/user.svelte';

  let { children } = $props();
  let backendStatus = $state<'checking' | 'connected' | 'error'>('checking');
  let isDarkMode = $state(true);
  let currentUser = $derived(userState.profile);
  let isSidebarCollapsed = $state(false);

  function toggleSidebar() {
    isSidebarCollapsed = !isSidebarCollapsed;
    localStorage.setItem('sidebar_collapsed', isSidebarCollapsed.toString());
  }

  function toggleTheme() {
    isDarkMode = !isDarkMode;
    if (isDarkMode) {
      document.documentElement.classList.add('dark');
      localStorage.setItem('theme', 'dark');
    } else {
      document.documentElement.classList.remove('dark');
      localStorage.setItem('theme', 'light');
    }
  }

  onMount(async () => {
    isSidebarCollapsed = localStorage.getItem('sidebar_collapsed') === 'true';
    if (localStorage.theme === 'dark' || (!('theme' in localStorage) && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
      isDarkMode = true;
      document.documentElement.classList.add('dark');
    } else {
      isDarkMode = false;
      document.documentElement.classList.remove('dark');
    }

    const token = localStorage.getItem('access_token');
    if (!token) { goto('/login'); return; }

    try {
      const res = await fetch('http://127.0.0.1:8000/health');
      backendStatus = res.ok ? 'connected' : 'error';
    } catch { backendStatus = 'error'; }

    try {
      const userRes = await fetch('http://127.0.0.1:8000/api/v1/users/me', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (userRes.ok) {
        userState.profile = await userRes.json();
        await alertState.refresh();
      } else {
        localStorage.removeItem('access_token');
        goto('/login');
      }
    } catch { /* session failed */ }
  });

  function handleLogout() {
    localStorage.removeItem('access_token');
    goto('/login');
  }
</script>

<div class="flex h-screen bg-gray-50 text-gray-900 dark:bg-black dark:text-gray-100 transition-colors duration-300">
  <!-- Sidebar -->
  <aside class={`transition-all duration-300 ease-in-out border-r border-gray-200 bg-white/70 dark:border-gray-800 dark:bg-gray-900/50 backdrop-blur-md hidden md:flex flex-col overflow-hidden ${isSidebarCollapsed ? 'w-20' : 'w-64'}`}>
    <div class="h-16 flex items-center px-6 border-b border-gray-200 dark:border-gray-800 shrink-0">
      <button onclick={toggleSidebar} class="flex items-center transition-all group">
        <Sun class="text-blue-600 dark:text-blue-500 w-6 h-6 shrink-0" />
        {#if !isSidebarCollapsed}
          <span class="ml-3 font-bold text-xl tracking-wide opacity-100 transition-all duration-300">SolShare</span>
        {/if}
      </button>
    </div>

    <nav class="flex-1 py-6 px-3 space-y-2 overflow-y-auto">
      <a href="/dashboard" class="group flex items-center px-3 py-2.5 rounded-lg text-gray-600 dark:text-gray-400 hover:bg-gray-100 hover:text-gray-900 dark:hover:bg-gray-800 dark:hover:text-white transition-all">
        <LayoutDashboard class="w-5 h-5 shrink-0" />
        {#if !isSidebarCollapsed}
          <span class="ml-3">Dashboard</span>
        {/if}
      </a>
      <a href="/buildings" class="group flex items-center px-3 py-2.5 rounded-lg text-gray-600 dark:text-gray-400 hover:bg-gray-100 hover:text-gray-900 dark:hover:bg-gray-800 dark:hover:text-white transition-all">
        <Building2 class="w-5 h-5 shrink-0" />
        {#if !isSidebarCollapsed}
          <span class="ml-3">Buildings</span>
        {/if}
      </a>
      <a href="/billing" class="group flex items-center px-3 py-2.5 rounded-lg text-gray-600 dark:text-gray-400 hover:bg-gray-100 hover:text-gray-900 dark:hover:bg-gray-800 dark:hover:text-white transition-all">
        <ReceiptText class="w-5 h-5 shrink-0" />
        {#if !isSidebarCollapsed}
          <span class="ml-3">Billing</span>
        {/if}
      </a>

      <!-- Alerts — badge uses shared alertState -->
      <a href="/alerts" class="group flex items-center px-3 py-2.5 rounded-lg text-gray-600 dark:text-gray-400 hover:bg-gray-100 hover:text-gray-900 dark:hover:bg-gray-800 dark:hover:text-white transition-all relative">
        <div class="relative shrink-0">
          <Bell class="w-5 h-5" />
          {#if alertState.unreadCount > 0}
            <span class="absolute -top-1.5 -right-1.5 min-w-[16px] h-4 px-1 bg-red-500 text-white text-[9px] font-bold rounded-full flex items-center justify-center animate-pulse">
              {alertState.unreadCount > 99 ? '99+' : alertState.unreadCount}
            </span>
          {/if}
        </div>
        {#if !isSidebarCollapsed}
          <span class="ml-3">Alerts</span>
          {#if alertState.unreadCount > 0}
            <span class="ml-auto text-[10px] bg-red-100 dark:bg-red-500/20 text-red-600 dark:text-red-400 px-1.5 py-0.5 rounded-full font-bold">
              {alertState.unreadCount}
            </span>
          {/if}
        {/if}
      </a>

      {#if currentUser?.role === 'admin'}
        <a href="/admin" class="group flex items-center px-3 py-2.5 rounded-lg text-gray-600 dark:text-gray-400 hover:bg-gray-100 hover:text-gray-900 dark:hover:bg-gray-800 dark:hover:text-white transition-all">
          <Shield class="w-5 h-5 shrink-0" />
          {#if !isSidebarCollapsed}
            <span class="ml-3 font-semibold">Admin Panel</span>
          {/if}
        </a>
      {/if}
      {#if currentUser?.role === 'admin' || currentUser?.role === 'property_manager'}
        <a href="/settings" class="group flex items-center px-3 py-2.5 rounded-lg text-gray-600 dark:text-gray-400 hover:bg-gray-100 hover:text-gray-900 dark:hover:bg-gray-800 dark:hover:text-white transition-all">
          <Settings class="w-5 h-5 shrink-0" />
          {#if !isSidebarCollapsed}
            <span class="ml-3">Settings</span>
          {/if}
        </a>
      {/if}
    </nav>

    <!-- User profile footer -->
    <div class="mt-auto border-t border-gray-200 dark:border-gray-800 p-4 shrink-0 overflow-hidden">
      {#if currentUser}
        <div class="flex items-center space-x-3 w-full">
          <div class="w-8 h-8 rounded-full bg-gradient-to-tr from-blue-500 to-indigo-500 flex items-center justify-center text-white font-bold shrink-0">
            {currentUser.full_name ? currentUser.full_name[0].toUpperCase() : currentUser.email[0].toUpperCase()}
          </div>
          {#if !isSidebarCollapsed}
            <div class="truncate flex-1">
              <p class="text-sm font-semibold text-gray-900 dark:text-white truncate">{currentUser.full_name || 'User'}</p>
              <p class="text-[10px] uppercase font-bold text-blue-500">{currentUser.role.replace('_', ' ')}</p>
            </div>
            <button onclick={handleLogout} class="p-1 text-gray-400 hover:text-red-500 transition-colors">
              <LogOut class="w-4 h-4" />
            </button>
          {/if}
        </div>
      {/if}
    </div>
  </aside>

  <!-- Main Content -->
  <div class="flex-1 flex flex-col overflow-hidden">
    <!-- Topbar -->
    <header class="h-16 border-b border-gray-200 bg-white/60 dark:border-gray-800 dark:bg-gray-900/40 backdrop-blur flex items-center justify-between px-6 shrink-0">
      <div></div>
      <div class="flex items-center space-x-4">
        {#if backendStatus === 'connected'}
          <span class="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-medium tracking-tight">API CONNECTED</span>
        {/if}
        <button onclick={toggleTheme} class="p-2 rounded-full bg-gray-100 hover:bg-gray-200 text-gray-600 dark:bg-gray-800/80 dark:hover:bg-gray-700 dark:text-gray-300 transition-colors shadow-sm">
          {#if isDarkMode}<Sun class="w-4 h-4 text-amber-500" />{:else}<Moon class="w-4 h-4 text-indigo-500" />{/if}
        </button>
      </div>
    </header>

    <!-- Page Content -->
    <main class="flex-1 overflow-y-auto p-6 bg-gray-50/50 dark:bg-black transition-colors duration-300">
      <div class="max-w-7xl mx-auto">
        {@render children()}
      </div>
    </main>
  </div>
</div>
