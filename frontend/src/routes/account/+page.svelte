<script lang="ts">
	import { enhance } from '$app/forms';
	import UserRound from 'lucide-svelte/icons/user-round';
	import Mail from 'lucide-svelte/icons/mail';
	import KeyRound from 'lucide-svelte/icons/key-round';
	import ShieldCheck from 'lucide-svelte/icons/shield-check';
	import LogOut from 'lucide-svelte/icons/log-out';

	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();
</script>

<svelte:head>
	<title>Account - AppGoblin</title>
</svelte:head>

<div class="container mx-auto max-w-2xl px-4 py-8">
	<div class="card preset-tonal p-6 md:p-8 space-y-6">
		<!-- Header -->
		<div class="flex items-center gap-4 pb-4 border-b border-surface-300-700">
			<div class="p-3 rounded-full bg-primary-500/20">
				<UserRound size={32} class="text-primary-500" />
			</div>
			<div>
				<h1 class="text-2xl font-bold">Hi, {data.user.username}!</h1>
				<p class="text-sm text-surface-600-400">Manage your account settings</p>
			</div>
		</div>

		<!-- Account Info -->
		<section class="space-y-4">
			<h2 class="text-lg font-semibold">Account Information</h2>

			<div class="flex items-center gap-3 p-4 rounded-lg bg-surface-100-900">
				<Mail size={20} class="text-surface-500" />
				<div>
					<p class="text-xs text-surface-500 uppercase tracking-wide">Email</p>
					<p class="font-medium">{data.user.email}</p>
				</div>
				{#if data.user.emailVerified}
					<span class="ml-auto badge preset-filled-success-900-100 text-xs">Verified</span>
				{:else}
					<a
						href="/auth/verify-email"
						class="ml-auto badge preset-filled-warning-500 text-xs hover:opacity-80"
					>
						Unverified - Click to verify
					</a>
				{/if}
			</div>
		</section>

		<!-- Security Section -->
		<section class="space-y-4">
			<h2 class="text-lg font-semibold">Security</h2>

			<div class="grid gap-3">
				<a
					href="/auth/settings"
					class="flex items-center gap-3 p-4 rounded-lg bg-surface-100-900 hover:bg-surface-200-800 transition-colors"
				>
					<KeyRound size={20} class="text-surface-500" />
					<div class="flex-1">
						<p class="font-medium">Password & Email</p>
						<p class="text-sm text-surface-500">Update your password or email address</p>
					</div>
					<span class="text-surface-400">→</span>
				</a>

				<a
					href="/auth/2fa/setup"
					class="flex items-center gap-3 p-4 rounded-lg bg-surface-100-900 hover:bg-surface-200-800 transition-colors"
				>
					<ShieldCheck size={20} class="text-surface-500" />
					<div class="flex-1">
						<p class="font-medium">Two-Factor Authentication</p>
						<p class="text-sm text-surface-500">
							{data.user.registered2FA
								? 'Manage your 2FA settings'
								: 'Add extra security to your account'}
						</p>
					</div>
					{#if data.user.registered2FA}
						<span class="badge preset-filled-success-900-100 text-xs">Enabled</span>
					{:else}
						<span class="badge preset-filled-surface-500 text-xs">Not set up</span>
					{/if}
				</a>

				{#if data.user.registered2FA}
					<a
						href="/auth/recovery-code"
						class="flex items-center gap-3 p-4 rounded-lg bg-surface-100-900 hover:bg-surface-200-800 transition-colors"
					>
						<KeyRound size={20} class="text-surface-500" />
						<div class="flex-1">
							<p class="font-medium">Recovery Code</p>
							<p class="text-sm text-surface-500">View your 2FA recovery code</p>
						</div>
						<span class="text-surface-400">→</span>
					</a>
				{/if}
			</div>
		</section>

		<!-- Subscription Section -->
		<section class="space-y-4">
			<h2 class="text-lg font-semibold">Subscription</h2>

			<div class="p-4 rounded-lg bg-surface-100-900 border border-surface-200-800">
				{#if data.subscription}
					<div class="flex justify-between items-center mb-4">
						<div>
							<p class="font-medium text-lg capitalize">
								{#if data.subscription.status === 'active' && data.subscription.cancel_at}
									Active (Cancels {new Date(data.subscription.cancel_at).toLocaleDateString()})
								{:else}
									{data.subscription.status}
								{/if}
							</p>
							{#if data.subscriptionTier}
								<p class="text-sm text-surface-500">Plan: {data.subscriptionTier}</p>
							{:else}
								<p class="text-sm text-surface-500">Plan: Unknown</p>
							{/if}
							<p class="text-sm text-surface-500">
								{#if data.subscription.cancel_at}
									Access available until end of period
								{:else}
									Renews on {new Date(data.subscription.current_period_end).toLocaleDateString()}
								{/if}
							</p>
						</div>
						<span
							class="badge text-white {data.subscription.status === 'active'
								? 'preset-filled-success-100-900'
								: 'preset-filled-warning-900-100'}"
						>
							{data.subscription.status.charAt(0).toUpperCase() + data.subscription.status.slice(1)}
						</span>
					</div>

					<form method="POST" action="?/portal" use:enhance>
						<button type="submit" class="btn preset-tonal w-full">Manage Subscription</button>
					</form>
				{:else}
					<div class="text-center py-4">
						<p class="text-surface-600-400 mb-2">Plan: Free</p>
						<a href="/pricing" class="btn preset-filled-primary-500">View Pricing</a>
					</div>
				{/if}
			</div>
		</section>

		<!-- Sign Out -->
		<section class="pt-4 border-t border-surface-300-700">
			<form method="post" action="?/logout" use:enhance>
				<button class="btn preset-tonal w-full flex items-center justify-center gap-2">
					<span class="flex items-center justify-center gap-2"> <LogOut size={18} /> Sign Out</span>
				</button>
			</form>
		</section>
	</div>
</div>
