<script lang="ts">
	import type { PageData } from './$types';
	import ShieldCheck from 'lucide-svelte/icons/shield-check';

	let { data }: { data: PageData } = $props();
</script>

<svelte:head>
	<title>Account - AppGoblin</title>
</svelte:head>

<div class="p-6 md:p-8 space-y-8">
	<div>
		<h1 class="text-2xl font-bold">Hello, {data.user.username}!</h1>
		<p class="text-sm">Welcome to your AppGoblin account</p>
	</div>

	<section class="space-y-4">
		<div class="grid gap-3 md:grid-cols-2">
			<!-- Subscription Status -->
			<div class="p-6 rounded-lg border border-surface-100-900">
				<h2 class="text-sm font-semibold text-surface-500 uppercase tracking-wide mb-2">
					Subscription Plan
				</h2>
				{#if data.subscription}
					<p class="font-bold text-xl capitalize">{data.subscription.status}</p>
					{#if data.subscriptionTier}
						<p class=" mt-1">{data.subscriptionTier}</p>
					{/if}
				{:else}
					<p class="font-bold text-xl">Free Plan</p>
					<p class=" mt-1">Upgrade for more limits</p>
				{/if}
			</div>

			<!-- Quick Security Status -->
			<div class="p-6 rounded-lg border border-surface-100-900">
				<h2 class="text-sm font-semibold text-surface-500 uppercase tracking-wide mb-2">
					Security Status
				</h2>
				<div class="flex items-center gap-2 mt-1">
					<ShieldCheck
						size={24}
						class={data.user.registered2FA ? 'text-success-500' : 'text-surface-400'}
					/>
					<div>
						<p class="font-bold">{data.user.registered2FA ? '2FA Enabled' : 'Add 2FA'}</p>
						<p class="text-sm">
							{data.user.registered2FA ? 'Your account is secure.' : 'Not set up yet.'}
						</p>
					</div>
				</div>
			</div>
		</div>
	</section>
</div>
