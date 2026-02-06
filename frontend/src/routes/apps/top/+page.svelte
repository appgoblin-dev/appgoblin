<script lang="ts">
	import X from 'lucide-svelte/icons/x';
	import Filter from 'lucide-svelte/icons/filter';
	import Search from 'lucide-svelte/icons/search';
	import Loader2 from 'lucide-svelte/icons/loader-2';
	import RotateCcw from 'lucide-svelte/icons/rotate-ccw';
	import { formatNumber } from '$lib/utils/formatNumber';
	import { enhance } from '$app/forms';
	import CrossfilterAppsTable from '$lib/CrossfilterAppsTable.svelte';

	// TanStack Table Imports
	import { type SortingState } from '@tanstack/table-core';

	interface Company {
		company_name: string;
		company_domain: string;
		total_apps: number;
	}

	interface Category {
		id: string;
		name: string;
		total_apps: number;
	}

	interface App {
		id: number;
		store_id: string;
		name: string;
		installs: number;
		rating_count: number;
		installs_d30: number;
		in_app_purchases: boolean;
		ad_supported: boolean;
		store: number;
		app_icon_url?: string;
	}

	let { data, form } = $props();

	// Safely access companies with fallback to empty array
	let companies = $derived<Company[]>(data.companies ?? []);
	let categories = $derived<Category[]>(data.categories ?? []);

	// Filter state
	let includeDomains = $state<string[]>([]);
	let excludeDomains = $state<string[]>([]);
	let requireSdkApi = $state(false);
	let requireIap = $state(false);
	let requireAds = $state(false);

	let selectedCategory = $state<string>('');
	let selectedStore = $state<number | ''>('');

	// Metric Filters
	let minInstalls = $state<number | null>(null);
	let maxInstalls = $state<number | null>(null);
	let minRatings = $state<number | null>(null);
	let maxRatings = $state<number | null>(null);
	let minMonthlyInstalls = $state<number | null>(null);
	let maxMonthlyInstalls = $state<number | null>(null);

	// Default to 6 months ago
	const sixMonthsAgo = new Date();
	sixMonthsAgo.setMonth(sixMonthsAgo.getMonth() - 6);
	let myDate = $state(sixMonthsAgo.toISOString().split('T')[0]);

	// Search state for dropdowns
	let includeSearch = $state('');
	let excludeSearch = $state('');
	let includeDropdownOpen = $state(false);
	let excludeDropdownOpen = $state(false);

	// Results state
	let isLoading = $state(false);
	let sorting = $state<SortingState>([{ id: 'installs', desc: true }]);

	const exportFilename = `appgoblin-crossfilter-${new Date().toISOString().split('T')[0]}`;
	const formApps = $derived(() => (form?.apps ?? []) as App[]);
	const formError = $derived(() => form?.error ?? '');
	const hasSearched = $derived(() => !!form?.success || !!form?.error);


	// Filtered companies for dropdowns - with null safety
	let filteredIncludeCompanies = $derived(() => {
		if (!companies || companies.length === 0) return [];
		const searchLower = (includeSearch ?? '').toLowerCase();
		return companies
			.filter((c) => {
				if (!c?.company_name || !c?.company_domain) return false;
				return (
					c.company_name.toLowerCase().includes(searchLower) ||
					c.company_domain.toLowerCase().includes(searchLower)
				);
			})
			.filter((c) => !includeDomains.includes(c.company_domain))
			.slice(0, 25);
	});

	let filteredExcludeCompanies = $derived(() => {
		if (!companies || companies.length === 0) return [];
		const searchLower = (excludeSearch ?? '').toLowerCase();
		return companies
			.filter((c) => {
				if (!c?.company_name || !c?.company_domain) return false;
				return (
					c.company_name.toLowerCase().includes(searchLower) ||
					c.company_domain.toLowerCase().includes(searchLower)
				);
			})
			.filter((c) => !excludeDomains.includes(c.company_domain))
			.slice(0, 25);
	});

	function addIncludeDomain(domain: string) {
		if (domain && !includeDomains.includes(domain)) {
			includeDomains = [...includeDomains, domain];
		}
		includeSearch = '';
		includeDropdownOpen = false;
	}

	function removeIncludeDomain(domain: string) {
		includeDomains = includeDomains.filter((d) => d !== domain);
	}

	function addExcludeDomain(domain: string) {
		if (domain && !excludeDomains.includes(domain)) {
			excludeDomains = [...excludeDomains, domain];
		}
		excludeSearch = '';
		excludeDropdownOpen = false;
	}

	function removeExcludeDomain(domain: string) {
		excludeDomains = excludeDomains.filter((d) => d !== domain);
	}

	function resetFilters() {
		includeDomains = [];
		excludeDomains = [];
		requireSdkApi = false;
		requireIap = false;
		requireAds = false;
		selectedCategory = '';
		selectedStore = '';
		minInstalls = null;
		maxInstalls = null;
		minRatings = null;
		maxRatings = null;
		minMonthlyInstalls = null;
		maxMonthlyInstalls = null;
		const sixMonthsAgo = new Date();
		sixMonthsAgo.setMonth(sixMonthsAgo.getMonth() - 6);
		myDate = sixMonthsAgo.toISOString().split('T')[0];
		isLoading = false;
	}

	function getCompanyName(domain: string): string {
		if (!domain) return 'Unknown';
		const company = companies.find((c) => c?.company_domain === domain);
		return company?.company_name || domain;
	}

</script>

<svelte:head>
	<title>Top Apps Analytics - AppGoblin</title>
	<meta
		name="description"
		content="Find top apps by SDK usage, monetization, and more. Filter by companies, IAP, ads, and SDK presence."
	/>
</svelte:head>

<div class="container mx-auto px-2 md:px-4 py-4 md:py-8">
	<div class="mb-6">
		<h1 class="text-2xl md:text-3xl font-bold text-primary-900-100">Top Apps Analytics</h1>
		<p class="text-sm md:text-base text-surface-600-400 mt-2">
			Find apps using specific SDKs, ad networks, and monetization strategies. Filter by company
			presence, in-app purchases, and ad support.
		</p>
	</div>

	<div class="grid grid-cols-2 lg:grid-cols-[320px_1fr] gap-4 md:gap-6">
		<!-- Sidebar Filters -->
		<aside
			class="card preset-tonal p-4 space-y-5 lg:sticky lg:top-20 overflow-y-auto "
		>
			<div class="flex items-center gap-2 pb-3 border-b border-surface-300-700">
				<Filter size={20} class="text-primary-500" />
				<h2 class="text-lg font-semibold">Filters</h2>
			</div>

			<form
				method="POST"
				action="?/search"
				use:enhance={({ formData }) => {
					// Manually append complex data structures
					formData.append('include_domains', JSON.stringify(includeDomains));
					formData.append('exclude_domains', JSON.stringify(excludeDomains));
					formData.append('require_sdk_api', requireSdkApi.toString());
					formData.append('require_iap', requireIap.toString());
					formData.append('require_ads', requireAds.toString());
					formData.append('mydate', myDate);
					if (selectedCategory) formData.append('category', selectedCategory);
					if (selectedStore) formData.append('store', selectedStore.toString());

					// Metrics
					if (minInstalls) formData.append('min_installs', minInstalls.toString());
					if (maxInstalls) formData.append('max_installs', maxInstalls.toString());
					if (minRatings) formData.append('min_rating_count', minRatings.toString());
					if (maxRatings) formData.append('max_rating_count', maxRatings.toString());
					if (minMonthlyInstalls)
						formData.append('min_installs_d30', minMonthlyInstalls.toString());
					if (maxMonthlyInstalls)
						formData.append('max_installs_d30', maxMonthlyInstalls.toString());

					// Sorting
					formData.append('sort_col', sorting[0]?.id || 'installs');
					formData.append('sort_order', sorting[0]?.desc ? 'desc' : 'asc');

				isLoading = true;

				return async ({ update }) => {
					await update({ reset: false }); // Don't reset form fields
					isLoading = false;
				};
				}}
				class="space-y-5"
			>
				<!-- Include Companies -->
				<div class="space-y-2">
					<label class="label font-medium text-sm" for="include-search"
						>Include Companies (Required)</label
					>
					<p class="text-xs text-surface-500">Apps must use ALL selected SDKs/companies</p>
					<div class="relative">
						<input
							type="text"
							id="include-search"
							class="input text-sm"
							placeholder="Search companies..."
							bind:value={includeSearch}
							onfocus={() => (includeDropdownOpen = true)}
							onblur={() => setTimeout(() => (includeDropdownOpen = false), 200)}
						/>
						{#if includeDropdownOpen && filteredIncludeCompanies().length > 0}
							<div
								class="absolute z-50 w-full mt-1 bg-surface-100-900 border border-surface-300-700 rounded-lg shadow-lg max-h-48 lg:max-h-92 overflow-y-auto"
							>
								{#each filteredIncludeCompanies() as company (company.company_domain)}
									<button
										type="button"
										class="w-full px-3 py-2 text-left text-sm hover:bg-surface-200-800 flex justify-between items-center"
										onmousedown={() => addIncludeDomain(company.company_domain)}
									>
										<span>{company.company_name}</span>
										<span class="text-xs text-surface-500"
											>{formatNumber(company.total_apps)} apps</span
										>
									</button>
								{/each}
							</div>
						{/if}
					</div>
					{#if includeDomains.length > 0}
						<div class="flex flex-wrap gap-1 mt-2">
							{#each includeDomains as domain}
								<span
									class="badge preset-filled-primary-500 text-xs flex items-center gap-1 px-2 py-1"
								>
									{getCompanyName(domain)}
									<button type="button" onclick={() => removeIncludeDomain(domain)} class="ml-1">
										<X size={12} />
									</button>
								</span>
							{/each}
						</div>
					{/if}
				</div>

				<!-- Exclude Companies -->
				<div class="space-y-2">
					<label class="label font-medium text-sm" for="exclude-search">Exclude Companies</label>
					<p class="text-xs text-surface-500">Apps must NOT use any of these</p>
					<div class="relative">
						<input
							type="text"
							id="exclude-search"
							class="input text-sm"
							placeholder="Search companies to exclude..."
							bind:value={excludeSearch}
							onfocus={() => (excludeDropdownOpen = true)}
							onblur={() => setTimeout(() => (excludeDropdownOpen = false), 200)}
						/>
						{#if excludeDropdownOpen && filteredExcludeCompanies().length > 0}
							<div
								class="absolute z-50 w-full mt-1 bg-surface-100-900 border border-surface-300-700 rounded-lg shadow-lg max-h-48 overflow-y-auto"
							>
								{#each filteredExcludeCompanies() as company (company.company_domain)}
									<button
										type="button"
										class="w-full px-3 py-2 text-left text-sm hover:bg-surface-200-800 flex justify-between items-center"
										onmousedown={() => addExcludeDomain(company.company_domain)}
									>
										<span>{company.company_name}</span>
										<span class="text-xs text-surface-500"
											>{formatNumber(company.total_apps)} apps</span
										>
									</button>
								{/each}
							</div>
						{/if}
					</div>
					{#if excludeDomains.length > 0}
						<div class="flex flex-wrap gap-1 mt-2">
							{#each excludeDomains as domain}
								<span
									class="badge preset-filled-error-900-100 text-xs flex items-center gap-1 px-2 py-1"
								>
									{getCompanyName(domain)}
									<button type="button" onclick={() => removeExcludeDomain(domain)} class="ml-1">
										<X size={12} />
									</button>
								</span>
							{/each}
						</div>
					{/if}
				</div>

				<!-- App Details -->
				<div class="space-y-2">
					<span class="label font-medium text-sm">App Details</span>
					<label class="label text-xs text-surface-500" for="store-select">Store</label>
					<select class="select text-sm" id="store-select" bind:value={selectedStore}>
						<option value="">Any Store</option>
						<option value="1">Google Play</option>
						<option value="2">Apple App Store</option>
					</select>

					<label class="label text-xs text-surface-500 mt-2" for="category-select">Category</label>
					<select class="select text-sm" id="category-select" bind:value={selectedCategory}>
						<option value="">Any Category</option>
						{#each categories as cat}
							<option value={cat.id}>{cat.name}</option>
						{/each}
					</select>
				</div>

				<!-- Metrics -->
				<div class="space-y-3">
					<span class="label font-medium text-sm">Metrics</span>

					<!-- Installs -->
					<div class="grid grid-cols-2 gap-2">
						<div class="space-y-1">
							<label class="text-xs text-surface-500" for="min-installs">Min Installs</label>
							<input
								type="number"
								id="min-installs"
								class="input text-sm px-2 py-1"
								placeholder="0"
								bind:value={minInstalls}
							/>
						</div>
						<div class="space-y-1">
							<label class="text-xs text-surface-500" for="max-installs">Max Installs</label>
							<input
								type="number"
								id="max-installs"
								class="input text-sm px-2 py-1"
								placeholder="NO MAX"
								bind:value={maxInstalls}
							/>
						</div>
					</div>

					<!-- Monthly Installs -->
					<div class="grid grid-cols-2 gap-2">
						<div class="space-y-1">
							<label class="text-xs text-surface-500" for="min-monthly">Min Monthly</label>
							<input
								type="number"
								id="min-monthly"
								class="input text-sm px-2 py-1"
								placeholder="0"
								bind:value={minMonthlyInstalls}
							/>
						</div>
						<div class="space-y-1">
							<label class="text-xs text-surface-500" for="max-monthly">Max Monthly</label>
							<input
								type="number"
								id="max-monthly"
								class="input text-sm px-2 py-1"
								placeholder="NO MAX"
								bind:value={maxMonthlyInstalls}
							/>
						</div>
					</div>

					<!-- Ratings -->
					<div class="grid grid-cols-2 gap-2">
						<div class="space-y-1">
							<label class="text-xs text-surface-500" for="min-ratings">Min Ratings</label>
							<input
								type="number"
								id="min-ratings"
								class="input text-sm px-2 py-1"
								placeholder="0"
								bind:value={minRatings}
							/>
						</div>
						<div class="space-y-1">
							<label class="text-xs text-surface-500" for="max-ratings">Max Ratings</label>
							<input
								type="number"
								id="max-ratings"
								class="input text-sm px-2 py-1"
								placeholder="NO MAX"
								bind:value={maxRatings}
							/>
						</div>
					</div>
				</div>

				<!-- Detection Type -->
				<div class="space-y-2">
					<span class="label font-medium text-sm">Detection Requirements</span>
					<label class="flex items-center gap-2 cursor-pointer">
						<input type="checkbox" class="checkbox" bind:checked={requireSdkApi} />
						<span class="text-sm">Require SDK or API detection</span>
					</label>
				</div>

				<!-- Monetization Filters -->
				<div class="space-y-2">
					<span class="label font-medium text-sm">Monetization</span>
					<label class="flex items-center gap-2 cursor-pointer">
						<input type="checkbox" class="checkbox" bind:checked={requireIap} />
						<span class="text-sm">Has In-App Purchases</span>
					</label>
					<label class="flex items-center gap-2 cursor-pointer">
						<input type="checkbox" class="checkbox" bind:checked={requireAds} />
						<span class="text-sm">Has Ads</span>
					</label>
				</div>

				<!-- Date Filter -->
				<div class="space-y-2">
					<label class="label font-medium text-sm" for="date-filter">Last Updated After</label>
					<input type="date" id="date-filter" class="input text-sm" bind:value={myDate} />
				</div>

				<!-- Action Buttons -->
				<div class="space-y-2">
					<button
						type="submit"
						class="btn preset-filled-primary-500 w-full flex items-center justify-center gap-2"
						disabled={isLoading || includeDomains.length === 0}
					>
						{#if isLoading}
							<Loader2 size={18} class="animate-spin" />
							Searching...
						{:else}
							<Search size={18} />
							Find Apps
						{/if}
					</button>

					<button
						type="button"
						class="btn preset-tonal w-full flex items-center justify-center gap-2 text-sm"
						onclick={resetFilters}
						disabled={isLoading}
					>
						<RotateCcw size={16} />
						Reset Filters
					</button>
				</div>
			</form>

			{#if formError()}
				<p class="text-error-900-100 text-sm text-center">{formError()}</p>
			{/if}

			<!-- Filter Summary -->
			{#if includeDomains.length > 0}
				<div class="text-xs text-surface-500 pt-2 border-t border-surface-300-700">
					<p>
						<strong>Query:</strong> Apps using {includeDomains.length} selected SDK{includeDomains.length >
						1
							? 's'
							: ''}
						{excludeDomains.length > 0 ? `, excluding ${excludeDomains.length}` : ''}
					</p>
				</div>
			{/if}
		</aside>

		<!-- Results Table -->
		<main class="card preset-tonal p-4 overflow-hidden">
		{#if !hasSearched()}
				<div class="text-center py-16 text-surface-500">
					<Filter size={48} class="mx-auto mb-4 opacity-50" />
					<p class="text-lg font-medium">Configure your filters</p>
					<p class="text-sm mt-2">
						Select companies to include, set your preferences, and click "Find Apps" to see results.
					</p>
				</div>
			{:else if isLoading}
				<div class="text-center py-16">
					<Loader2 size={48} class="mx-auto mb-4 animate-spin text-primary-500" />
					<p class="text-lg font-medium">Searching apps...</p>
				</div>
		{:else if form?.success && formApps().length === 0}
				<div class="text-center py-16 text-surface-500">
					<X size={48} class="mx-auto mb-4 opacity-50" />
					<p class="text-lg font-medium">No apps found</p>
					<p class="text-sm mt-2">Try adjusting your filters to find more apps.</p>
				</div>
			{:else}
				<div class="mb-4 flex items-center justify-between flex-wrap gap-2">
					<p class="text-sm text-surface-600-400">
					Found <strong>{formApps().length}</strong> apps matching your criteria
					</p>
				</div>
			{#if form?.success}
				<CrossfilterAppsTable apps={formApps()} filename={exportFilename} bind:sorting />
			{/if}
			{/if}
		</main>
	</div>
</div>
