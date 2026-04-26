<script lang="ts">
	import { page } from '$app/state';
	import type { SearchResponse } from '../../../types';
	import AppGroupCard from '$lib/AppGroupCard.svelte';
	import CompaniesSearchTable from '$lib/CompaniesSearchTable.svelte';
	import { Tabs } from '@skeletonlabs/skeleton-svelte';

	interface Props {
		data: SearchResponse;
	}

	let { data }: Props = $props();
	const searchTerm = $derived(page.params.term || '');

	// App store filter state
	type AppStore = 'apple' | 'google';
	let selectedStore = $state<AppStore>('google');

	// Computed values
	const appleAppCount = $derived(
		typeof data.appGroupByStore !== 'string' ? data.appGroupByStore.apple.apps.length : 0
	);
	const googleAppCount = $derived(
		typeof data.appGroupByStore !== 'string' ? data.appGroupByStore.google.apps.length : 0
	);
	const totalAppCount = $derived(appleAppCount + googleAppCount);
	const companiesCount = $derived(
		typeof data.companiesResults !== 'string' ? data.companiesResults.length : 0
	);

	// Determine default tab based on results
	const defaultTab = $derived(
		totalAppCount === 0 && companiesCount > 0
			? 'companies'
			: totalAppCount > 0 && companiesCount === 0
				? 'apps'
				: 'apps' // If both have results, default to apps
	);

	// Auto-select store with results
	$effect(() => {
		if (selectedStore === 'apple' && appleAppCount === 0 && googleAppCount > 0) {
			selectedStore = 'google';
		} else if (selectedStore === 'google' && googleAppCount === 0 && appleAppCount > 0) {
			selectedStore = 'apple';
		}
	});
</script>

<div class="space-y-6 p-4 md:px-32">
	<!-- Header -->
	<div class="card p-4 md:p-6">
		<h1 class="text-2xl md:text-3xl mb-4">
			Search Results for: <span class="font-bold">'{searchTerm}'</span>
		</h1>

		<!-- Summary Stats -->
		<div class="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
			<div class="preset-filled-surface-100-900 p-3">
				<div class="text-sm">Apps Found</div>
				<div class="text-2xl font-bold">{totalAppCount}</div>
				<div class="text-xs mt-1">
					{appleAppCount} Apple • {googleAppCount} Google Play
				</div>
			</div>
			<div class="preset-filled-surface-100-900 p-3">
				<div class="text-sm">Companies Found</div>
				<div class="text-2xl font-bold">{companiesCount}</div>
				<div class="text-xs mt-1">Adtech/Business/Development Tools</div>
			</div>
		</div>
	</div>

	<!-- Main Tabs: Apps vs Companies -->
	<div>
		<Tabs defaultValue={defaultTab}>
			<Tabs.List>
				<Tabs.Trigger value="apps" class="p-0 md:p-8">
					<p class="text-xs md:text-base">
						Apps
						{#if totalAppCount > 0}
							<span
								class="ml-2 px-2 py-0.5 text-xs rounded-full bg-primary-900-100 text-surface-50-950"
							>
								{totalAppCount}
							</span>
						{/if}
					</p>
				</Tabs.Trigger>
				<Tabs.Trigger value="companies" class="p-0 md:p-8">
					<p class="text-xs md:text-base">
						Companies
						{#if companiesCount > 0}
							<span
								class="ml-2 px-2 py-0.5 text-xs rounded-full bg-primary-900-100 text-surface-50-950"
							>
								{companiesCount}
							</span>
						{/if}
					</p>
				</Tabs.Trigger>
				<Tabs.Indicator />
			</Tabs.List>

			<Tabs.Content value="apps">
				{#if typeof data.appGroupByStore === 'string'}
					<div class="preset-filled-surface-100-900 p-4">
						<p class="text-error-500">Search failed. Please try again.</p>
					</div>
				{:else if totalAppCount === 0}
					<div class="preset-filled-surface-100-900 p-6 text-center">
						<h2 class="h3 mb-4">No Apps Found</h2>
						<p class=" mb-4">
							No apps found for <span class="font-semibold">'{searchTerm}'</span>, but a search has
							been queued. Full data from app stores, if it exists, should be available in the
							coming days.
						</p>
						<p class="text-sm">Reach out on Discord or GitHub if you have any questions.</p>
					</div>
				{:else}
					<!-- Store Filter (Apple vs Google) -->
					{#if appleAppCount > 0 && googleAppCount > 0}
						<div class="mb-6 flex gap-2">
							<button
								type="button"
								class="px-4 py-2 rounded-md font-medium transition-colors {selectedStore === 'apple'
									? 'bg-primary-900-100 text-surface-50-950'
									: 'bg-surface-200-800  hover:bg-surface-300-700'}"
								onclick={() => {
									selectedStore = 'apple';
								}}
							>
								App Store ({appleAppCount})
							</button>
							<button
								type="button"
								class="px-4 py-2 rounded-md font-medium transition-colors {selectedStore ===
								'google'
									? 'bg-primary-900-100 text-surface-50-950'
									: 'bg-surface-200-800  hover:bg-surface-300-700'}"
								onclick={() => {
									selectedStore = 'google';
								}}
							>
								Google Play ({googleAppCount})
							</button>
						</div>
					{/if}

					<!-- App Results -->
					{#if selectedStore === 'apple' && appleAppCount > 0}
						<AppGroupCard apps={data.appGroupByStore.apple} />
					{:else if selectedStore === 'google' && googleAppCount > 0}
						<AppGroupCard apps={data.appGroupByStore.google} />
					{:else}
						<div class="preset-filled-surface-100-900 p-4">
							<p class="">
								No apps found for {selectedStore === 'apple' ? 'App Store' : 'Google Play'}.
							</p>
						</div>
					{/if}

					<!-- Help Text -->
					<div class="preset-filled-surface-100-900 p-4 mt-6">
						<h3 class="h4 mb-2">Didn't see the app you're looking for?</h3>
						<p class="text-sm">
							This search checks both Google Play and App Store. If an app exists but isn't showing
							up, it may be queued for indexing and should appear within the next day. Reach out on
							Discord or GitHub if you have questions or need support.
						</p>
					</div>
				{/if}
			</Tabs.Content>

			<Tabs.Content value="companies">
				{#if typeof data.companiesResults === 'string'}
					<div class="preset-filled-surface-100-900 p-4">
						<p class="text-error-500">Search failed. Please try again.</p>
					</div>
				{:else if companiesCount === 0}
					<div class="preset-filled-surface-100-900 p-6 text-center">
						<h2 class="h3 mb-4">No Companies Found</h2>
						<p class=" mb-4">
							No adtech/business/development tool companies found matching
							<span class="font-semibold"> '{searchTerm}'</span>.
						</p>
						<p class="text-sm">
							If you expected to see something, please let us know by sending a note on Discord or
							GitHub and we can add it.
						</p>
					</div>
				{:else}
					<div>
						<h3 class="h4 mb-4">Companies and Domains Matching: '{searchTerm}'</h3>
						<CompaniesSearchTable data={data.companiesResults} />
					</div>
				{/if}
			</Tabs.Content>
		</Tabs>
	</div>
</div>
