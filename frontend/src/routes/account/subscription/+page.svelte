<script lang="ts">
	import { enhance } from '$app/forms';
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();
</script>

<svelte:head>
	<title>Subscription - AppGoblin</title>
</svelte:head>

<div class="p-6 md:p-8 space-y-8">
	<div>
		<h1 class="text-2xl font-bold">Subscription</h1>
		<p class="text-sm">Manage your billing and subscription plan</p>
	</div>

	<section class="space-y-4">
		<div class="p-6 rounded-lg border border-surface-100-900">
			{#if data.subscription}
				<div class="flex justify-between items-start mb-6">
					<div>
						{#if data.subscription.status === 'active' && data.subscription.cancel_at}
							<p class="text-sm text-warning-700-300 font-medium mb-1">
								Active (Cancels {new Date(data.subscription.cancel_at).toLocaleDateString()})
							</p>
						{:else}
							<p class="font-bold text-xl capitalize mb-1">
								{data.subscription.status}
							</p>
						{/if}

						{#if data.subscriptionTier}
							<p class="text-surface-500">Plan: {data.subscriptionTier}</p>
						{:else}
							<p class="text-surface-500">Plan: Unknown</p>
						{/if}

						<div class="mt-2">
							{#if data.subscription.cancel_at}
								<p class="text-sm text-warning-700-300">Access available until end of period</p>
							{:else}
								<p class="text-sm text-surface-500">
									Renews on {new Date(data.subscription.current_period_end).toLocaleDateString()}
								</p>
							{/if}
						</div>
					</div>
					<span
						class="badge px-3 py-1 font-medium {data.subscription.status === 'active'
							? 'preset-filled-success-500'
							: 'preset-filled-warning-500'}"
					>
						{data.subscription.status.charAt(0).toUpperCase() + data.subscription.status.slice(1)}
					</span>
				</div>

				<form method="POST" action="?/portal" use:enhance>
					<button type="submit" class="btn preset-tonal w-full sm:w-auto"
						>Manage Subscription at Stripe</button
					>
				</form>
			{:else}
				<div class="text-center py-8">
					<div class="mb-4">
						<h3 class="text-lg font-bold">Free Plan</h3>
						<p class=" mt-2">You are currently on the free plan.</p>
					</div>
					<a href="/pricing" class="btn preset-filled-primary-500">View Pricing & Upgrade</a>
				</div>
			{/if}
		</div>
	</section>
</div>
