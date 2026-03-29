<script lang="ts">
  import { Sun, LogIn, Mail, Lock, AlertCircle } from 'lucide-svelte';
  import Button from '$lib/components/ui/Button.svelte';
  import { goto } from '$app/navigation';

  let email = $state('');
  let password = $state('');
  let errorMsg = $state('');
  let isLoading = $state(false);

  async function handleLogin(e: Event) {
    e.preventDefault();
    errorMsg = '';
    isLoading = true;
    
    try {
      const formData = new URLSearchParams();
      formData.append('username', email);
      formData.append('password', password);

      const response = await fetch('http://127.0.0.1:8000/api/v1/auth/token', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: formData
      });

      if (response.ok) {
        const data = await response.json();
        localStorage.setItem('access_token', data.access_token);
        goto('/dashboard');
      } else {
        const errData = await response.json();
        errorMsg = errData.detail || 'Login failed';
      }
    } catch (e) {
      errorMsg = 'Could not connect to FastAPI server';
    } finally {
      isLoading = false;
    }
  }
</script>

<div class="flex min-h-screen items-center justify-center bg-black bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-gray-800 via-black to-black">
  <div class="w-full max-w-md p-8 rounded-2xl border border-gray-800 bg-gray-900/60 backdrop-blur-xl shadow-2xl">
    <div class="flex flex-col items-center mb-8">
      <div class="p-3 bg-blue-500/10 rounded-full mb-4 ring-1 ring-blue-500/30">
        <Sun class="text-blue-500 w-10 h-10" />
      </div>
      <h1 class="text-3xl font-extrabold text-white tracking-tight">SolShare</h1>
      <p class="text-sm text-gray-400 mt-2">Sign in to manage energy distribution</p>
    </div>

    <form onsubmit={handleLogin} class="space-y-6">
      {#if errorMsg}
        <div class="flex items-center space-x-2 p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-red-500 text-sm">
          <AlertCircle class="w-4 h-4" />
          <span>{errorMsg}</span>
        </div>
      {/if}

      <div class="space-y-4">
        <div class="relative">
          <Mail class="absolute left-3 top-3.5 h-5 w-5 text-gray-500" />
          <input type="email" bind:value={email} placeholder="Email address" class="w-full bg-black/50 border border-gray-700 rounded-lg py-3 pl-10 pr-4 text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all outline-none" required />
        </div>
        <div class="relative">
          <Lock class="absolute left-3 top-3.5 h-5 w-5 text-gray-500" />
          <input type="password" bind:value={password} placeholder="Password" class="w-full bg-black/50 border border-gray-700 rounded-lg py-3 pl-10 pr-4 text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all outline-none" required />
        </div>
      </div>
      
      <div class="flex items-center justify-between">
        <label class="flex items-center space-x-2 text-sm text-gray-400">
          <input type="checkbox" class="rounded border-gray-700 bg-black/50 text-blue-500 focus:ring-blue-500/50" />
          <span>Remember me</span>
        </label>
        <a href="/login/forgot" class="text-sm text-blue-400 hover:text-blue-300">Forgot password?</a>
      </div>

      <button type="submit" disabled={isLoading} class="w-full flex justify-center items-center py-3 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-medium rounded-lg transition-colors">
        <LogIn class="mr-2 h-5 w-5" /> {isLoading ? 'Signing in...' : 'Sign In'}
      </button>
    </form>
    
    <div class="mt-8 text-center text-sm text-gray-500">
      Don't have an account? <a href="/register" class="text-blue-400 hover:underline">Request access</a>
    </div>
  </div>
</div>
