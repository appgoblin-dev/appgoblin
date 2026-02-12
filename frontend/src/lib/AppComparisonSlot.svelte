<script lang="ts">
	import AppComparisonColumn from '$lib/AppComparisonColumn.svelte';
	import ComparisonSearch from '$lib/ComparisonSearch.svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';

	let {
		app = null,
		history = null,
		histogram = null,
		sdks = null,
		companyTypes = null,
		onAppSelected,
		slotId = '1',
		searchResult = null
	}: {
		app?: any;
		history?: any;
		histogram?: any;
		sdks?: any;
		companyTypes?: any;
		onAppSelected: (app: any) => void;
		slotId?: string;
		searchResult?: any;
	} = $props();

	let isSearching = $state(true);
	let isLoading = $state(false);
	let manuallyToggledSearch = $state(false);

	// Check if there's a search query in the URL
	let hasSearchQuery = $derived(!!$page.url.searchParams.get(`search${slotId}`));

	$effect(() => {
		// Only auto-manage search state if user hasn't manually toggled it
		// and there's no active search query in the URL
		if (!manuallyToggledSearch && !hasSearchQuery) {
			if (app) {
				isSearching = false;
				isLoading = false;
			} else {
				isSearching = true;
				isLoading = false;
			}
		} else if (hasSearchQuery) {
			// If there's a search query in URL, ensure we're in search mode
			isSearching = true;
			isLoading = false;
		}
	});

	function handleSelect(app: any) {
		isLoading = true; // Show loading state while navigating
		manuallyToggledSearch = false; // Reset manual toggle when selecting an app
		onAppSelected(app);
		isSearching = false;
	}

	function toggleSearch() {
		manuallyToggledSearch = true;
		isSearching = !isSearching;

		// When opening search, clear the search param to start fresh
		if (isSearching) {
			const url = new URL($page.url);
			url.searchParams.delete(`search${slotId}`);
			goto(url.pathname + url.search, { noScroll: true, keepFocus: true, invalidateAll: false });
		}
	}
</script>

<div
	class="h-full flex flex-col rounded-lg bg-white p-1 md:p-4 shadow-sm dark:bg-surface-800 border dark:border-gray-700"
>
	{#if isLoading}
		<div class="flex-1 flex flex-col items-center justify-center p-8">
			<div
				class="h-10 w-10 animate-spin rounded-full border-4 border-surface-200 border-t-primary-500"
			></div>
			<p class="mt-4 text-surface-600-400 font-medium">Loading app...</p>
		</div>
	{:else if app && !isSearching && !hasSearchQuery}
		<div class="mb-4 flex justify-end">
			<button
				class="text-xs font-semibold text-primary-600 hover:text-primary-800 dark:text-primary-400 dark:hover:text-primary-300 underline"
				onclick={toggleSearch}
			>
				Change App
			</button>
		</div>
		<AppComparisonColumn {app} {history} {histogram} {sdks} {companyTypes} />
	{:else}
		<div class="flex-1 flex flex-col">
			<div class="mb-4 flex justify-between items-center">
				<h3 class="font-bold text-lg">Select App</h3>
				{#if app}
					<button class="text-xs text-red-500 hover:underline" onclick={toggleSearch}>Cancel</button
					>
				{/if}
			</div>
			<div class="flex-1 min-h-[400px]">
				<ComparisonSearch onSelect={handleSelect} {slotId} {searchResult} />
			</div>
		</div>
	{/if}
</div>
