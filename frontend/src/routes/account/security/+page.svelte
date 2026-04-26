<script lang="ts">
	import type { PageData } from './$types';
	import ShieldCheck from 'lucide-svelte/icons/shield-check';
	import KeyRound from 'lucide-svelte/icons/key-round';

	let { data }: { data: PageData } = $props();
</script>

<svelte:head>
	<title>Security - AppGoblin</title>
</svelte:head>

<div class="p-6 md:p-8 space-y-8">
	<div>
		<h1 class="text-2xl font-bold">Security</h1>
		<p class="text-sm">Manage your account security and authentication methods</p>
	</div>

	<section class="space-y-4">
		<div class="grid gap-3">
			<a
				href="/auth/2fa/setup"
				class="flex items-center gap-3 p-4 rounded-lg border border-surface-100-900 hover:bg-surface-200-800 transition-colors"
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
					class="flex items-center gap-3 p-4 rounded-lg border border-surface-100-900 hover:bg-surface-200-800 transition-colors"
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
</div>
