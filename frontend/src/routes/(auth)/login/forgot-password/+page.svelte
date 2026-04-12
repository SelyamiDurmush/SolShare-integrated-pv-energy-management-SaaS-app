<script lang="ts">
    import {
        Sun,
        Mail,
        ArrowLeft,
        LoaderCircle,
        CircleAlert,
        CircleCheck,
    } from "lucide-svelte";
    import { goto } from "$app/navigation";

    let email = $state("");
    let statusMessage = $state("");
    let errorMsg = $state("");
    let isLoading = $state(false);
    let isSuccess = $state(false);

    async function handleRequestReset(event: SubmitEvent) {
        event.preventDefault();
        errorMsg = "";
        statusMessage = "";
        isLoading = true;
        isSuccess = false;

        try {
            const response = await fetch("/api/v1/auth/forgot-password", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email }),
            });

            const result = await response.json();

            if (response.ok) {
                statusMessage =
                    result.message ||
                    "If an account exists, an email has been sent.";
                isSuccess = true;
            } else {
                errorMsg =
                    result.detail || "An error occurred. Please try again.";
            }
        } catch (e) {
            errorMsg = "An error occurred. Please try again.";
        } finally {
            isLoading = false;
        }
    }
</script>

<div
    class="solshare-reset-wrapper flex min-h-screen items-center justify-center bg-black bg-[radial-gradient(ellipse_at_top,var(--tw-gradient-stops))] from-gray-800 via-black to-black"
>
    <div
        class="w-full max-w-md p-8 rounded-2xl border border-gray-800 bg-gray-900/60 backdrop-blur-xl shadow-2xl transition-all duration-500"
    >
        <div class="flex flex-col items-center mb-8">
            <div
                class="p-3 bg-blue-500/10 rounded-full mb-4 ring-1 ring-blue-500/30"
            >
                <Sun class="text-blue-500 w-10 h-10" />
            </div>
            <h1 class="text-3xl font-extrabold text-white tracking-tight">
                SolShare
            </h1>
            <p class="text-sm text-gray-400 mt-2 text-center">
                Enter your user account's verified email address and we will
                send you a password reset link.
            </p>
        </div>

        {#if isSuccess}
            <div
                class="mb-6 p-4 rounded-xl bg-green-500/10 border border-green-500/20 text-green-400 text-sm flex items-start space-x-3 animate-in fade-in slide-in-from-top-1 duration-300"
            >
                <CircleCheck class="w-5 h-5 shrink-0 mt-0.5" />
                <span>{statusMessage}</span>
            </div>
        {:else if errorMsg}
            <div
                class="mb-6 p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-500 text-sm flex items-start space-x-3 animate-in fade-in slide-in-from-top-1 duration-300"
            >
                <CircleAlert class="w-5 h-5 shrink-0 mt-0.5" />
                <span>{errorMsg}</span>
            </div>
        {/if}

        <form onsubmit={handleRequestReset} class="space-y-6">
            <div class="space-y-2">
                <label
                    for="email"
                    class="text-sm font-medium text-gray-300 ml-1"
                    >Email address</label
                >
                <div class="relative">
                    <Mail
                        class="absolute left-3 top-3.5 h-5 w-5 text-gray-500"
                    />
                    <input
                        id="email"
                        type="email"
                        bind:value={email}
                        placeholder="name@example.com"
                        class="w-full bg-black/50 border border-gray-700 rounded-lg py-3 pl-10 pr-4 text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all outline-none placeholder:text-gray-600"
                        required
                        disabled={isLoading || isSuccess}
                    />
                </div>
            </div>

            <button
                type="submit"
                disabled={isLoading || isSuccess}
                class="w-full flex justify-center items-center py-3 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-medium rounded-lg transition-all duration-300 hover:shadow-[0_0_20px_-5px_rgba(37,99,235,0.4)]"
            >
                {#if isLoading}
                    <LoaderCircle class="mr-2 h-5 w-5 animate-spin" />
                    Sending Link...
                {:else}
                    Send Password Reset Email
                {/if}
            </button>
        </form>

        <div class="mt-8 text-center border-t border-gray-800 pt-6">
            <a
                href="/login"
                class="inline-flex items-center text-sm font-medium text-gray-400 hover:text-blue-400 transition-colors group"
            >
                <ArrowLeft
                    class="mr-2 h-4 w-4 transition-transform group-hover:-translate-x-1"
                />
                Back to sign in
            </a>
        </div>
    </div>
</div>
