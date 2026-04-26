<script lang="ts">
	import { enhance } from '$app/forms';
	import type { PageData } from './$types';
	import Mail from 'lucide-svelte/icons/mail';
	import KeyRound from 'lucide-svelte/icons/key-round';
	import LogOut from 'lucide-svelte/icons/log-out';

	let { data }: { data: PageData } = $props();
</script>

<svelte:head>
	<title>Settings - AppGoblin</title>
</svelte:head>

<div class="p-6 md:p-8 space-y-8">
	<div>
		<h1 class="text-2xl font-bold">Settings</h1>
		<p class="text-sm">Manage your profile and account preferences</p>
	</div>

	<!-- Account Info -->
	<section class="space-y-4">
		<h2 class="text-lg font-semibold">Account Information</h2>
		<div class="flex items-center gap-3 p-4 rounded-lg border border-surface-100-900">
			<Mail size={20} class="text-surface-500" />
			<div>
				<p class="text-xs text-surface-500 uppercase tracking-wide">Email</p>
				<p class="font-medium">{data.user.email}</p>
			</div>
			{#if data.user.emailVerified}
				<span class="ml-auto badge preset-filled-success-300-700 text-xs">Verified</span>
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

	<section class="space-y-4">
		<h2 class="text-lg font-semibold">Change Details</h2>
		<a
			href="/auth/settings"
			class="flex items-center gap-3 p-4 rounded-lg border border-surface-100-900 hover:bg-surface-200-800 transition-colors"
		>
			<KeyRound size={20} class="text-surface-500" />
			<div class="flex-1">
				<p class="font-medium">Password & Email</p>
				<p class="text-sm text-surface-500">Update your password or email address</p>
			</div>
			<span class="text-surface-400">→</span>
		</a>
	</section>

	<section class="pt-6 border-t border-surface-300-700">
		<form method="post" action="?/logout" use:enhance>
			<button class="btn preset-tonal w-full sm:w-auto flex items-center justify-center gap-2">
				<span class="flex items-center justify-center gap-2"> <LogOut size={18} /> Sign Out</span>
			</button>
		</form>
	</section>
</div>
