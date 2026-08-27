<script lang="ts">
	import { page } from '$app/state';
	import type { SearchResponse } from '../../../types';
	import AppGroupCard from '$lib/AppGroupCard.svelte';
	import CompaniesSearchTable from '$lib/CompaniesSearchTable.svelte';
	import StoreIcon from '$lib/StoreIcon.svelte';
	import { Tabs } from '@skeletonlabs/skeleton-svelte';

	interface Props {
		data: SearchResponse;
	}

	let { data }: Props = $props();
	const searchTerm = $derived(page.params.term || '');

	// Computed values
	const appleAppCount = $derived(
		typeof data.appGroupByStore !== 'string' ? data.appGroupByStore.apple.apps.length : 0
	);
	const googleAppCount = $derived(
		typeof data.appGroupByStore !== 'string' ? data.appGroupByStore.google.apps.length : 0
	);
	const companiesCount = $derived(
		typeof data.companiesResults !== 'string' ? data.companiesResults.length : 0
	);

	// Error state — API returns a string when the search itself failed
	const appError = $derived(typeof data.appGroupByStore === 'string');
	const companiesError = $derived(typeof data.companiesResults === 'string');

	// Which tabs to show (only tabs with results are displayed)
	const showApple = $derived(appleAppCount > 0);
	const showGoogle = $derived(googleAppCount > 0);
	const showCompanies = $derived(companiesCount > 0);
	const hasAnyResults = $derived(showApple || showGoogle || showCompanies);
	const hasAnyError = $derived(appError || companiesError);

	// Determine default tab — prefer iOS when available, fall through each option
	const defaultTab = $derived(
		showGoogle ? 'google' : showApple ? 'apple' : showCompanies ? 'companies' : 'google'
	);
</script>

<svelte:head>
	<title>Search results for "{searchTerm}" - AppGoblin</title>
	<meta name="robots" content="noindex, follow" />
	<link rel="canonical" href={page.url.href} />
</svelte:head>

<div class="space-y-6 p-4 md:px-32">
	<!-- Header -->
	<div class="card p-4 md:p-6">
		<h1 class="text-2xl md:text-3xl mb-2">
			Search Results for: <span class="font-bold">'{searchTerm}'</span>
		</h1>
		<p class="text-sm opacity-80">
			Results are split into <span class="font-medium">Android Google Play</span>,
			<span class="font-medium">iOS App Store</span>, and
			<span class="font-medium">Companies & Domains</span>. Only tabs with results are shown.
		</p>
	</div>

	<!-- Three flat tabs: iOS | Android | Companies -->
	{#if hasAnyError}
		<div class="preset-filled-error-100-900 p-4">
			<p class="font-medium">Something went wrong with the search.</p>
			{#if appError}
				<p class="text-sm mt-1">App search: {data.appGroupByStore}</p>
			{/if}
			{#if companiesError}
				<p class="text-sm mt-1">Companies search: {data.companiesResults}</p>
			{/if}
		</div>
	{:else if hasAnyResults}
		<div>
			<Tabs defaultValue={defaultTab}>
				<Tabs.List>
					{#if showGoogle}
						<Tabs.Trigger value="google" class="p-0 md:p-8">
							<p class="inline-flex items-center gap-1 md:gap-2 text-xs md:text-xl">
								<StoreIcon store={1} />
								Google Play
								<span class="md:ml-2 px-2 py-0.5 text-xs rounded-full bg-primary-100-900">
									{googleAppCount}
								</span>
							</p>
						</Tabs.Trigger>
					{/if}
					{#if showApple}
						<Tabs.Trigger value="apple" class="p-0 md:p-8">
							<p class="inline-flex items-center gap-1 md:gap-2 text-xs md:text-xl">
								<StoreIcon store={2} />
								iOS
								<span class="ml-0 md:ml-2 px-2 py-0.5 text-xs rounded-full bg-primary-100-900">
									{appleAppCount}
								</span>
							</p>
						</Tabs.Trigger>
					{/if}
					{#if showCompanies}
						<Tabs.Trigger value="companies" class="p-0 md:gap-2 md:p-8">
							<p class="text-xs md:text-xl">
								Companies & Domains
								<span class="md:ml-2 px-2 py-0.5 text-xs rounded-full bg-primary-100-900">
									{companiesCount}
								</span>
							</p>
						</Tabs.Trigger>
					{/if}
					<Tabs.Indicator />
				</Tabs.List>

				<Tabs.Content value="apple">
					<AppGroupCard apps={data.appGroupByStore.apple} />
					<div class="preset-filled-surface-100-900 p-4 mt-6">
						<h3 class="h4 mb-2">Didn't see the iOS app you're looking for?</h3>
						<p class="text-sm">
							If an app exists but isn't showing up, it may be queued for indexing and should appear
							within the next day.
						</p>
					</div>
				</Tabs.Content>

				<Tabs.Content value="google">
					<AppGroupCard apps={data.appGroupByStore.google} />
					<div class="preset-filled-surface-100-900 p-4 mt-6">
						<h3 class="h4 mb-2">Didn't see the Android app you're looking for?</h3>
						<p class="text-sm">
							If an app exists but isn't showing up, it may be queued for indexing and should appear
							within the next day.
						</p>
					</div>
				</Tabs.Content>

				<Tabs.Content value="companies">
					<div class="md:px-32">
						<CompaniesSearchTable data={data.companiesResults} />
					</div>
				</Tabs.Content>
			</Tabs>
		</div>
	{:else}
		<!-- No results at all across any section -->
		<div class="preset-filled-surface-100-900 p-6 text-center">
			<h2 class="h3 mb-4">No Results Found</h2>
			<p class=" mb-4">
				No apps or companies found for <span class="font-semibold">'{searchTerm}'</span>. Searches
				are queued for indexing and results should appear within the coming days if the data exists.
			</p>
		</div>
	{/if}

	<!-- Shared footer note -->
	<div class="preset-filled-surface-100-900 p-4 text-sm opacity-80">
		Have a question or expect a result you don't see?
		<a href="/contact" class="underline underline-offset-2 hover:opacity-100">Contact us</a> and we'll
		take a look.
	</div>
</div>
