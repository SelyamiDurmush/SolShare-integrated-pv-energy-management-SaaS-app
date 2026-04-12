<script lang="ts">
    import { page } from "$app/stores";
    import {
        Sun,
        Lock,
        KeyRound,
        ArrowLeft,
        LoaderCircle,
        CircleAlert,
        CircleCheck,
    } from "lucide-svelte";

    // Automatically grab the token from the URL: ?token=XYZ123
    let token = $page.url.searchParams.get("token");

    let newPassword = $state("");
    let confirmPassword = $state("");
    let statusMessage = $state("");
    let errorMsg = $state("");
    let isLoading = $state(false);
    let isSuccess = $state(false);

    async function handleResetPassword(event: SubmitEvent) {
        event.preventDefault();
        errorMsg = "";
        statusMessage = "";

        // Client-side validation
        if (newPassword !== confirmPassword) {
            errorMsg = "Passwords do not match! Please try again.";
            return;
        }

        if (newPassword.length < 8) {
            errorMsg = "Password must be at least 8 characters long.";
            return;
        }

        isLoading = true;

        try {
            const response = await fetch("/api/v1/auth/reset-password", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ token, new_password: newPassword }),
            });

            const result = await response.json();
            if (response.ok) {
                statusMessage =
                    "Password successfully updated! You can now log in.";
                isSuccess = true;
            } else {
                errorMsg = result.detail || "Invalid or expired token.";
            }
        } catch (error) {
            errorMsg = "Server error. Please try again or request a new link.";
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
                Set New Password
            </h1>
            <p class="text-sm text-gray-400 mt-2 text-center">
                Please enter your new secure password below.
            </p>
        </div>

        {#if !token}
            <div
                class="mb-6 p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-500 text-sm flex flex-col items-center text-center space-y-3"
            >
                <CircleAlert class="w-8 h-8" />
                <p>
                    Invalid or missing reset token. Please request a new
                    password reset link.
                </p>
                <a
                    href="/login/forgot-password"
                    class="mt-2 w-full py-2 bg-gray-800 hover:bg-gray-700 text-white rounded-lg transition-colors"
                >
                    Request New Link
                </a>
            </div>
        {:else if isSuccess}
            <div
                class="mb-6 p-4 rounded-xl bg-green-500/10 border border-green-500/20 text-green-400 text-sm flex items-start space-x-3 animate-in fade-in slide-in-from-top-1 duration-300"
            >
                <CircleCheck class="w-5 h-5 shrink-0 mt-0.5" />
                <span>{statusMessage}</span>
            </div>
            <a
                href="/login"
                class="w-full flex justify-center items-center py-3 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-all duration-300 shadow-lg"
            >
                Proceed to Login
            </a>
        {:else}
            {#if errorMsg}
                <div
                    class="mb-6 p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-500 text-sm flex items-start space-x-3 animate-in fade-in slide-in-from-top-1 duration-300"
                >
                    <CircleAlert class="w-5 h-5 shrink-0 mt-0.5" />
                    <span>{errorMsg}</span>
                </div>
            {/if}

            <form onsubmit={handleResetPassword} class="space-y-6">
                <div class="space-y-2">
                    <label
                        for="new-password"
                        class="text-sm font-medium text-gray-300 ml-1"
                        >New Password</label
                    >
                    <div class="relative">
                        <Lock
                            class="absolute left-3 top-3.5 h-5 w-5 text-gray-500"
                        />
                        <input
                            id="new-password"
                            type="password"
                            bind:value={newPassword}
                            placeholder="••••••••"
                            required
                            disabled={isLoading}
                            class="w-full bg-black/50 border border-gray-700 rounded-lg py-3 pl-10 pr-4 text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all outline-none placeholder:text-gray-600"
                        />
                    </div>
                </div>

                <div class="space-y-2">
                    <label
                        for="confirm-password"
                        class="text-sm font-medium text-gray-300 ml-1"
                        >Confirm Password</label
                    >
                    <div class="relative">
                        <KeyRound
                            class="absolute left-3 top-3.5 h-5 w-5 text-gray-500"
                        />
                        <input
                            id="confirm-password"
                            type="password"
                            bind:value={confirmPassword}
                            placeholder="••••••••"
                            required
                            disabled={isLoading}
                            class="w-full bg-black/50 border border-gray-700 rounded-lg py-3 pl-10 pr-4 text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all outline-none placeholder:text-gray-600"
                        />
                    </div>
                </div>

                <button
                    type="submit"
                    disabled={isLoading}
                    class="w-full flex justify-center items-center py-3 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-medium rounded-lg transition-all duration-300 hover:shadow-[0_0_20px_-5px_rgba(37,99,235,0.4)]"
                >
                    {#if isLoading}
                        <LoaderCircle class="mr-2 h-5 w-5 animate-spin" />
                        Saving...
                    {:else}
                        Save New Password
                    {/if}
                </button>
            </form>
        {/if}

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
