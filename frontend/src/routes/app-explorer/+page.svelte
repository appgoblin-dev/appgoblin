<script lang="ts">
	import X from 'lucide-svelte/icons/x';
	import Filter from 'lucide-svelte/icons/filter';
	import Search from 'lucide-svelte/icons/search';
	import Loader2 from 'lucide-svelte/icons/loader-2';
	import RotateCcw from 'lucide-svelte/icons/rotate-ccw';
	import { formatNumber } from '$lib/utils/formatNumber';
	import { countryCodeToEmoji } from '$lib/utils/countryCodeToEmoji';
	import { enhance } from '$app/forms';
	import CrossfilterAppsTable from '$lib/CrossfilterAppsTable.svelte';
	import WhiteCard from '$lib/WhiteCard.svelte';

	import type { CatData, CrossfilterApp } from '../.././types';

	// TanStack Table Imports
	import { type SortingState } from '@tanstack/table-core';

	interface Company {
		company_name: string;
		company_domain: string;
		total_apps: number;
	}

	let { data, form } = $props();

	const hasPaidAccess = $derived(data.hasPaidAccess ?? false);
	const hasB2BSdkAccess = $derived(data.hasB2BSdkAccess ?? false);

	// Safely access companies with fallback to empty array
	let companies = $derived<Company[]>(data.companies ?? []);
	let categories = $derived<CatData>(data.categories ?? []);
	let rankingCountries = $derived<{ code: string; name: string }[]>(
		(() => {
			const countriesData = data.countries;

			if (!countriesData) return [];

			if (Array.isArray(countriesData)) {
				return countriesData
					.filter((country) => country?.code && country?.name)
					.map((country) => ({ code: country.code, name: country.name }));
			}

			if (typeof countriesData === 'object') {
				return Object.entries(countriesData as Record<string, string>).map(([code, name]) => ({
					code,
					name
				}));
			}

			return [];
		})()
	);

	// Filter state
	let includeDomains = $state<string[]>([]);
	let excludeDomains = $state<string[]>([]);
	let requireSdkApi = $state(false);
	let requireIap = $state(false);
	let requireAds = $state(false);

	let selectedCategory = $state<string>('');
	let selectedStore = $state<number | ''>('');
	let rankingFilter = $state<string>('');

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
	const formApps = $derived(() => (form?.apps ?? []) as CrossfilterApp[]);
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
		rankingFilter = '';
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
	<title>App Explorer - AppGoblin</title>
	<meta
		name="description"
		content="Powerful app discovery tool for sales teams. Find apps using specific SDKs, ad networks, and monetization strategies."
	/>
</svelte:head>

<div class="container mx-auto px-2 md:px-4 py-4 md:py-8">
	<div class="mb-6">
		<h1 class="text-2xl md:text-3xl font-bold text-primary-900-100">App Explorer</h1>
		<p class="text-sm md:text-base text-surface-600-400 mt-2">
			Powerful app discovery and filtering tool for sales teams, market researchers, and app
			developers.
		</p>
	</div>

	{#if !hasPaidAccess}
		<!-- Explanatory Content - Only shown to non-paid users -->
		<WhiteCard>
			{#snippet title()}
				<span>About App Explorer / App CrossFilter / App Query</span>
			{/snippet}
			<div class="p-4 flex flex-col gap-4">
				<div class="space-y-3">
					<p>
						The <strong>App Explorer</strong> (also known as <strong>App CrossFilter</strong> or
						<strong>App Query</strong>) is a powerful tool that allows you to discover and filter
						mobile apps based on multiple criteria simultaneously.
					</p>

					<div>
						<h3 class="font-semibold text-lg mb-2">Key Features:</h3>
						<ul class="list-disc list-inside space-y-2 text-sm">
							<li>
								<strong>SDK & Company Filtering:</strong> Find apps that use specific SDKs or companies
								(include/exclude multiple companies)
							</li>
							<li>
								<strong>Monetization Filters:</strong> Filter by in-app purchases, ad support, and SDK/API
								detection requirements
							</li>
							<li>
								<strong>Store & Category:</strong> Narrow down by app store (Google Play, Apple App Store)
								and category
							</li>
							<li>
								<strong>Metrics Filtering:</strong> Filter by install counts, rating counts, and monthly
								installs with min/max ranges
							</li>
							<li>
								<strong>Date Filtering:</strong> Find apps updated after a specific date
							</li>
							<li>
								<strong>Export Results:</strong> Download filtered results as CSV for further analysis
							</li>
						</ul>
					</div>

					<div>
						<h3 class="font-semibold text-lg mb-2">Use Cases:</h3>
						<ul class="list-disc list-inside space-y-2 text-sm">
							<li>
								<strong>Sales Teams:</strong> Find potential customers by identifying apps using competitor
								SDKs or specific technologies
							</li>
							<li>
								<strong>Market Research:</strong> Analyze app ecosystems by filtering apps with specific
								monetization strategies
							</li>
							<li>
								<strong>Competitive Analysis:</strong> Discover apps in your category that use certain
								SDKs or ad networks
							</li>
							<li>
								<strong>Partnership Opportunities:</strong> Identify apps that could benefit from your
								SDK or service
							</li>
						</ul>
					</div>

					<div class="mt-4 p-4 bg-surface-100-900 rounded-lg border border-surface-300-700">
						<p class="text-sm mb-3">
							<strong>Access Required:</strong> The App Explorer is available to paid subscribers at
							any level. Please
							<a href="/pricing" class="underline hover:text-primary-600-400"
								>upgrade your account</a
							> to use this tool.
						</p>
						<a href="/pricing" class="btn preset-filled-primary-500 inline-flex items-center gap-2">
							<svg
								xmlns="http://www.w3.org/2000/svg"
								width="18"
								height="18"
								viewBox="0 0 24 24"
								fill="none"
								stroke="currentColor"
								stroke-width="2"
								stroke-linecap="round"
								stroke-linejoin="round"
								aria-hidden="true"
							>
								<rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
								<path d="M7 11V7a5 5 0 0 1 10 0v4" />
							</svg>
							<span>View Pricing Plans</span>
						</a>
					</div>
				</div>
			</div>
		</WhiteCard>
	{/if}

	<div class="mt-6">
		{#if hasPaidAccess}
			<h2 class="text-xl md:text-2xl font-bold text-primary-900-100 mb-4">Start Exploring</h2>
		{:else}
			<h2 class="text-xl md:text-2xl font-bold text-primary-900-100 mb-4">Preview</h2>
		{/if}
	</div>

	<div class="grid grid-cols-2 lg:grid-cols-[320px_1fr] gap-4 md:gap-6">
		<!-- Sidebar Filters -->
		<aside class="card preset-tonal p-4 space-y-5 lg:sticky lg:top-20 overflow-y-auto">
			<div class="flex items-center gap-2 pb-3 border-b border-surface-300-700">
				<Filter size={20} class="text-primary-500" />
				<h2 class="text-lg font-semibold">Filters</h2>
			</div>

			{#if !hasPaidAccess}
				<div class="mb-4 p-3 bg-warning-900-100/20 rounded-lg border border-warning-500">
					<p class="text-xs text-warning-900-100 flex items-center gap-2">
						<svg
							xmlns="http://www.w3.org/2000/svg"
							width="16"
							height="16"
							viewBox="0 0 24 24"
							fill="none"
							stroke="currentColor"
							stroke-width="2"
							stroke-linecap="round"
							stroke-linejoin="round"
						>
							<rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
							<path d="M7 11V7a5 5 0 0 1 10 0v4" />
						</svg>
						Filters are disabled. Upgrade to unlock.
					</p>
				</div>
			{/if}

			<form
				method="POST"
				action="?/search"
				use:enhance={hasPaidAccess
					? ({ formData }) => {
							// Manually append complex data structures
							formData.append(
								'include_domains',
								JSON.stringify(hasB2BSdkAccess ? includeDomains : [])
							);
							formData.append(
								'exclude_domains',
								JSON.stringify(hasB2BSdkAccess ? excludeDomains : [])
							);
							formData.append('require_sdk_api', requireSdkApi.toString());
							formData.append('require_iap', requireIap.toString());
							formData.append('require_ads', requireAds.toString());
							if (rankingFilter) formData.append('ranking_country', rankingFilter);
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

							isLoading = true;

							return async ({ update }) => {
								await update({ reset: false }); // Don't reset form fields
								isLoading = false;
							};
						}
					: undefined}
				class="space-y-5"
			>
				<div class="space-y-4 p-3 rounded-lg border border-surface-300-700 bg-surface-100-900/40">
					<h3 class="font-semibold text-sm uppercase tracking-wide text-surface-700-300">
						App Details & Metrics
					</h3>

					<!-- App Details -->
					<div class="space-y-2">
						<label class="label text-xs text-surface-500" for="store-select">Store</label>
						<select class="select text-sm" id="store-select" bind:value={selectedStore}>
							<option value="">Any Store</option>
							<option value="1">Google Play</option>
							<option value="2">Apple App Store</option>
						</select>

						<label class="label text-xs text-surface-500 mt-2" for="category-select">Category</label
						>
						<select class="select text-sm" id="category-select" bind:value={selectedCategory}>
							<option value="">Any Category</option>
							{#each categories.categories as cat}
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
								<label class="text-xs text-surface-500" for="min-monthly"
									>Min Monthly Installs</label
								>
								<input
									type="number"
									id="min-monthly"
									class="input text-sm px-2 py-1"
									placeholder="0"
									bind:value={minMonthlyInstalls}
								/>
							</div>
							<div class="space-y-1">
								<label class="text-xs text-surface-500" for="max-monthly"
									>Max Monthly Installs</label
								>
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

					<!-- Current Ranking Filter -->
					<div class="space-y-2">
						<label class="label font-medium text-sm" for="ranking-filter"
							>Apps that Are Currently Ranking</label
						>
						<p class="text-xs text-surface-500">
							Leave unset for all apps, choose overall for any ranking country, or choose one
							specific country.
						</p>
						<select class="select text-sm" id="ranking-filter" bind:value={rankingFilter}>
							<option value="">All apps (no ranking filter)</option>
							<option value="overall">Overall (ranked in at least one country)</option>
							{#each rankingCountries as country}
								<option value={country.code}>
									{countryCodeToEmoji(country.code)}
									{country.name}
								</option>
							{/each}
						</select>
					</div>
				</div>

				<div class="space-y-4 p-3 rounded-lg border border-surface-300-700 bg-surface-100-900/40">
					<h3 class="font-semibold text-sm uppercase tracking-wide text-surface-700-300">
						Company Filters
					</h3>

					{#if !hasB2BSdkAccess}
						<div class="p-3 rounded-lg border border-warning-500 bg-warning-900-100/20">
							<p class="text-xs text-warning-900-100">
								Company include/exclude filters are available on the B2B SDK tier.
								<a href="/pricing" class="underline hover:text-primary-600-400">Upgrade</a>
								to unlock.
							</p>
						</div>
					{/if}

					<!-- Include Companies -->
					<div class="space-y-2">
						<label class="label font-medium text-sm" for="include-search">Include Companies</label>
						<p class="text-xs text-surface-500">Apps must use ALL selected SDKs/companies</p>
						<div class="relative">
							<input
								type="text"
								id="include-search"
								class="input text-sm {!hasPaidAccess || !hasB2BSdkAccess
									? 'opacity-50 cursor-not-allowed'
									: ''}"
								placeholder="Search companies..."
								bind:value={includeSearch}
								disabled={!hasPaidAccess || !hasB2BSdkAccess}
								onfocus={() => hasPaidAccess && hasB2BSdkAccess && (includeDropdownOpen = true)}
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
								class="input text-sm {!hasPaidAccess || !hasB2BSdkAccess
									? 'opacity-50 cursor-not-allowed'
									: ''}"
								placeholder="Search companies to exclude..."
								bind:value={excludeSearch}
								disabled={!hasPaidAccess || !hasB2BSdkAccess}
								onfocus={() => hasPaidAccess && hasB2BSdkAccess && (excludeDropdownOpen = true)}
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
					<!-- Detection Type -->
					<div class="space-y-2">
						<span class="label font-medium text-sm">Detection Requirements</span>
						<label class="flex items-center gap-2 cursor-pointer">
							<input type="checkbox" class="checkbox" bind:checked={requireSdkApi} />
							<span class="text-sm">Require SDK or API detection</span>
						</label>
					</div>
				</div>

				<!-- Action Buttons -->
				<div class="space-y-2">
					<button
						type="submit"
						class="btn preset-filled-primary-500 w-full flex items-center justify-center gap-2"
						disabled={!hasPaidAccess || isLoading}
					>
						{#if !hasPaidAccess}
							<svg
								xmlns="http://www.w3.org/2000/svg"
								width="18"
								height="18"
								viewBox="0 0 24 24"
								fill="none"
								stroke="currentColor"
								stroke-width="2"
								stroke-linecap="round"
								stroke-linejoin="round"
							>
								<rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
								<path d="M7 11V7a5 5 0 0 1 10 0v4" />
							</svg>
							Locked - Upgrade Required
						{:else if isLoading}
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
			{#if !hasPaidAccess}
				<div class="text-center py-16 relative">
					<div class="absolute inset-0 flex items-center justify-center opacity-10">
						<Filter size={120} class="text-surface-500" />
					</div>
					<div class="relative z-10">
						<svg
							xmlns="http://www.w3.org/2000/svg"
							width="64"
							height="64"
							viewBox="0 0 24 24"
							fill="none"
							stroke="currentColor"
							stroke-width="2"
							stroke-linecap="round"
							stroke-linejoin="round"
							class="mx-auto mb-4 text-surface-500"
						>
							<rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
							<path d="M7 11V7a5 5 0 0 1 10 0v4" />
						</svg>
						<p class="text-lg font-medium mb-2">Results Area Locked</p>
						<p class="text-sm text-surface-600-400 mb-4">
							App search results will appear here once you upgrade. Configure filters on the left to
							see what you can discover.
						</p>
						<a href="/pricing" class="btn preset-filled-primary-500 inline-flex items-center gap-2">
							<svg
								xmlns="http://www.w3.org/2000/svg"
								width="18"
								height="18"
								viewBox="0 0 24 24"
								fill="none"
								stroke="currentColor"
								stroke-width="2"
								stroke-linecap="round"
								stroke-linejoin="round"
								aria-hidden="true"
							>
								<rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
								<path d="M7 11V7a5 5 0 0 1 10 0v4" />
							</svg>
							<span>Upgrade to Unlock</span>
						</a>
					</div>
				</div>
			{:else if !hasSearched()}
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
