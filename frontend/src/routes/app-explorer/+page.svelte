<script lang="ts">
	import X from 'lucide-svelte/icons/x';
	import Filter from 'lucide-svelte/icons/filter';
	import Search from 'lucide-svelte/icons/search';
	import Mail from 'lucide-svelte/icons/mail';
	import Loader2 from 'lucide-svelte/icons/loader-2';
	import RotateCcw from 'lucide-svelte/icons/rotate-ccw';
	import { countryCodeToEmoji } from '$lib/utils/countryCodeToEmoji';
	import { applyAction, enhance } from '$app/forms';
	import {
		Combobox,
		Portal,
		type ComboboxRootProps,
		useListCollection
	} from '@skeletonlabs/skeleton-svelte';
	import CrossfilterAppsTable from '$lib/CrossfilterAppsTable.svelte';

	import type { CatData, CrossfilterApp, Countries } from '../.././types';

	// TanStack Table Imports
	import { type SortingState } from '@tanstack/table-core';

	interface Company {
		company_name: string;
		company_domain: string;
		total_apps: number;
	}

	interface CompanyOption {
		label: string;
		value: string;
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
				return Object.entries(countriesData as Countries).map(([code, value]) => ({
					code,
					name: value.langen
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

	// Company combobox state
	let includeItems = $state<CompanyOption[]>([]);
	let excludeItems = $state<CompanyOption[]>([]);

	// Results state
	let isLoading = $state(false);
	let isExporting = $state(false);
	let exportFeedback = $state('');
	let exportError = $state('');
	let sorting = $state<SortingState>([{ id: 'installs', desc: true }]);

	const exportFilename = `appgoblin-crossfilter-${new Date().toISOString().split('T')[0]}`;
	const formApps = $derived(() => (form?.apps ?? []) as CrossfilterApp[]);
	const formError = $derived(() => form?.error ?? '');
	const hasSearched = $derived(() => !!form?.success || !!form?.error);

	function appendFilterFields(formData: FormData) {
		formData.set('include_domains', JSON.stringify(hasB2BSdkAccess ? includeDomains : []));
		formData.set('exclude_domains', JSON.stringify(hasB2BSdkAccess ? excludeDomains : []));
		formData.set('require_sdk_api', requireSdkApi.toString());
		formData.set('require_iap', requireIap.toString());
		formData.set('require_ads', requireAds.toString());
		formData.set('mydate', myDate);

		if (rankingFilter) {
			formData.set('ranking_country', rankingFilter);
		} else {
			formData.delete('ranking_country');
		}

		if (selectedCategory) {
			formData.set('category', selectedCategory);
		} else {
			formData.delete('category');
		}

		if (selectedStore) {
			formData.set('store', selectedStore.toString());
		} else {
			formData.delete('store');
		}

		if (minInstalls != null) {
			formData.set('min_installs', minInstalls.toString());
		} else {
			formData.delete('min_installs');
		}

		if (maxInstalls != null) {
			formData.set('max_installs', maxInstalls.toString());
		} else {
			formData.delete('max_installs');
		}

		if (minRatings != null) {
			formData.set('min_rating_count', minRatings.toString());
		} else {
			formData.delete('min_rating_count');
		}

		if (maxRatings != null) {
			formData.set('max_rating_count', maxRatings.toString());
		} else {
			formData.delete('max_rating_count');
		}

		if (minMonthlyInstalls != null) {
			formData.set('min_installs_d30', minMonthlyInstalls.toString());
		} else {
			formData.delete('min_installs_d30');
		}

		if (maxMonthlyInstalls != null) {
			formData.set('max_installs_d30', maxMonthlyInstalls.toString());
		} else {
			formData.delete('max_installs_d30');
		}
	}

	function getActionStringField(
		data: Record<string, unknown> | null | undefined,
		key: string
	): string {
		const value = data?.[key];
		return typeof value === 'string' ? value : '';
	}

	const companyOptions = $derived.by<CompanyOption[]>(() => {
		if (!companies || companies.length === 0) return [];
		return companies
			.filter((company) => company?.company_name && company?.company_domain)
			.map((company) => ({
				label: company.company_name,
				value: company.company_domain
			}));
	});

	function getAvailableCompanyOptions(selectedDomains: string[]): CompanyOption[] {
		return companyOptions
			.filter((company) => !selectedDomains.includes(company.value))
			.slice(0, 25);
	}

	const includeCollection = $derived(
		useListCollection({
			items: includeItems,
			itemToString: (item) => item.label,
			itemToValue: (item) => item.value
		})
	);

	const excludeCollection = $derived(
		useListCollection({
			items: excludeItems,
			itemToString: (item) => item.label,
			itemToValue: (item) => item.value
		})
	);

	const onIncludeOpenChange = () => {
		includeItems = getAvailableCompanyOptions(includeDomains);
	};

	const onExcludeOpenChange = () => {
		excludeItems = getAvailableCompanyOptions(excludeDomains);
	};

	const onIncludeInputValueChange: ComboboxRootProps['onInputValueChange'] = (event) => {
		const searchValue = event.inputValue.toLowerCase();
		const options = getAvailableCompanyOptions(includeDomains);
		const filtered = options.filter(
			(item) =>
				item.label.toLowerCase().includes(searchValue) ||
				item.value.toLowerCase().includes(searchValue)
		);
		includeItems = filtered.length > 0 ? filtered : options;
	};

	const onExcludeInputValueChange: ComboboxRootProps['onInputValueChange'] = (event) => {
		const searchValue = event.inputValue.toLowerCase();
		const options = getAvailableCompanyOptions(excludeDomains);
		const filtered = options.filter(
			(item) =>
				item.label.toLowerCase().includes(searchValue) ||
				item.value.toLowerCase().includes(searchValue)
		);
		excludeItems = filtered.length > 0 ? filtered : options;
	};

	const onIncludeValueChange: ComboboxRootProps['onValueChange'] = (event) => {
		includeDomains = event.value as string[];
		includeItems = getAvailableCompanyOptions(includeDomains);
	};

	const onExcludeValueChange: ComboboxRootProps['onValueChange'] = (event) => {
		excludeDomains = event.value as string[];
		excludeItems = getAvailableCompanyOptions(excludeDomains);
	};

	function addIncludeDomain(domain: string) {
		if (domain && !includeDomains.includes(domain)) {
			includeDomains = [...includeDomains, domain];
		}
		includeItems = getAvailableCompanyOptions(includeDomains);
	}

	function removeIncludeDomain(domain: string) {
		includeDomains = includeDomains.filter((d) => d !== domain);
		includeItems = getAvailableCompanyOptions(includeDomains);
	}

	function addExcludeDomain(domain: string) {
		if (domain && !excludeDomains.includes(domain)) {
			excludeDomains = [...excludeDomains, domain];
		}
		excludeItems = getAvailableCompanyOptions(excludeDomains);
	}

	function removeExcludeDomain(domain: string) {
		excludeDomains = excludeDomains.filter((d) => d !== domain);
		excludeItems = getAvailableCompanyOptions(excludeDomains);
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
		isExporting = false;
		exportFeedback = '';
		exportError = '';
		includeItems = getAvailableCompanyOptions([]);
		excludeItems = getAvailableCompanyOptions([]);
	}

	function getCompanyName(domain: string): string {
		if (!domain) return 'Unknown';
		const company = companies.find((c) => c?.company_domain === domain);
		return company?.company_name || domain;
	}

	$effect(() => {
		includeItems = getAvailableCompanyOptions(includeDomains);
	});

	$effect(() => {
		excludeItems = getAvailableCompanyOptions(excludeDomains);
	});
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
		<h1 class="text-2xl md:text-3xl font-bold">App Explorer</h1>
		<p class="text-sm md:text-base mt-2">
			Powerful app discovery and filtering tool for sales teams, market researchers, and app
			developers.
		</p>
	</div>

	<div class="grid grid-cols-2 lg:grid-cols-[320px_1fr] gap-4 md:gap-6">
		<!-- Sidebar Filters -->
		<aside class="p-4 space-y-5 lg:sticky lg:top-20 overflow-y-auto">
			{#if !hasPaidAccess}
				<div class="mb-4 p-3 bg-warning-50-950/20 rounded-lg border border-warning-500">
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

			<div class="flex items-center gap-2 pb-3 border-b border-surface-300-700">
				<Filter size={20} class="text-primary-500" />
				<h2 class="text-lg font-semibold">Filters</h2>
			</div>

			<form
				method="POST"
				action="?/search"
				use:enhance={hasPaidAccess
					? ({ formData, submitter }) => {
							appendFilterFields(formData);
							const intent = submitter?.getAttribute('data-intent') ?? 'search';
							exportFeedback = '';
							exportError = '';

							isLoading = intent === 'search';
							isExporting = intent === 'email-export';

							return async ({ result, update }) => {
								if (intent === 'email-export') {
									if (result.type === 'redirect' || result.type === 'error') {
										await applyAction(result);
									} else if (result.type === 'success') {
										const actionData = result.data as Record<string, unknown>;
										exportFeedback =
											getActionStringField(actionData, 'exportMessage') || 'CSV export queued.';
										exportError = getActionStringField(actionData, 'error');
									} else if (result.type === 'failure') {
										const actionData = result.data as Record<string, unknown>;
										exportError =
											getActionStringField(actionData, 'error') || 'Failed to queue CSV export';
									}
								} else {
									await update({ reset: false }); // Don't reset form fields
								}
								isLoading = false;
								isExporting = false;
							};
						}
					: undefined}
				class="space-y-5"
			>
				<div class="space-y-4 p-3 rounded-lg border border-surface-300-700">
					<h3 class="font-semibold text-sm uppercase tracking-wide">App Details & Metrics</h3>

					<!-- App Details -->
					<div class="space-y-2">
						<label class="label text-xs" for="store-select">Store</label>
						<select class="select text-sm" id="store-select" bind:value={selectedStore}>
							<option value="">Any Store</option>
							<option value="1">Google Play</option>
							<option value="2">Apple App Store</option>
						</select>

						<label class="label text-xs mt-2" for="category-select">Category</label>
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
								<label class="text-xs" for="min-installs">Min Installs</label>
								<input
									type="number"
									id="min-installs"
									class="input text-sm px-2 py-1"
									placeholder="0"
									bind:value={minInstalls}
								/>
							</div>
							<div class="space-y-1">
								<label class="text-xs" for="max-installs">Max Installs</label>
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
								<label class="text-xs" for="min-monthly">Min Monthly Installs</label>
								<input
									type="number"
									id="min-monthly"
									class="input text-sm px-2 py-1"
									placeholder="0"
									bind:value={minMonthlyInstalls}
								/>
							</div>
							<div class="space-y-1">
								<label class="text-xs" for="max-monthly">Max Monthly Installs</label>
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
								<label class="text-xs" for="min-ratings">Min Ratings</label>
								<input
									type="number"
									id="min-ratings"
									class="input text-sm px-2 py-1"
									placeholder="0"
									bind:value={minRatings}
								/>
							</div>
							<div class="space-y-1">
								<label class="text-xs" for="max-ratings">Max Ratings</label>
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
				</div>

				<div class="space-y-4 p-3 rounded-lg border border-surface-300-700">
					<h3 class="font-semibold text-sm uppercase tracking-wide">App Store Ranks</h3>
					<div class="space-y-2">
						<label class="label font-medium text-sm" for="ranking-filter">Ranking Filter</label>
						<p class="text-xs">
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

				<div class="space-y-4 p-3 rounded-lg border border-surface-300-700">
					<h3 class="font-semibold text-sm uppercase tracking-wide">Company Filters</h3>

					{#if !hasB2BSdkAccess}
						<div class="p-3 rounded-lg border border-warning-500 bg-warning-50-950/20">
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
						<p class="text-xs">Apps must use ALL selected SDKs/companies</p>
						<Combobox
							placeholder="Search companies..."
							collection={includeCollection}
							onOpenChange={onIncludeOpenChange}
							onInputValueChange={onIncludeInputValueChange}
							value={includeDomains}
							onValueChange={onIncludeValueChange}
							class="w-full {!hasPaidAccess || !hasB2BSdkAccess
								? 'opacity-50 cursor-not-allowed'
								: ''}"
							multiple
							disabled={!hasPaidAccess || !hasB2BSdkAccess}
						>
							<Combobox.Control>
								<Combobox.Input id="include-search" />
								<Combobox.Trigger />
							</Combobox.Control>
							<Portal>
								<Combobox.Positioner>
									<Combobox.Content
										class="bg-surface-100-900 border border-surface-300-700 rounded-lg shadow-lg p-1 w-[min(22rem,calc(100vw-2rem))] max-h-48 lg:max-h-92 overflow-y-auto"
									>
										{#if includeItems.length > 0}
											{#each includeItems as item (item.value)}
												<Combobox.Item
													{item}
													class="flex justify-between items-center rounded px-3 py-2 text-sm hover:bg-surface-200-800"
												>
													<div class="min-w-0">
														<Combobox.ItemText>{item.label}</Combobox.ItemText>
													</div>
													<Combobox.ItemIndicator />
												</Combobox.Item>
											{/each}
										{:else}
											<p class="px-3 py-2 text-sm opacity-70">No matching companies</p>
										{/if}
									</Combobox.Content>
								</Combobox.Positioner>
							</Portal>
						</Combobox>

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
						<p class="text-xs">Apps must NOT use any of these</p>
						<Combobox
							placeholder="Search companies to exclude..."
							collection={excludeCollection}
							onOpenChange={onExcludeOpenChange}
							onInputValueChange={onExcludeInputValueChange}
							value={excludeDomains}
							onValueChange={onExcludeValueChange}
							class="w-full {!hasPaidAccess || !hasB2BSdkAccess
								? 'opacity-50 cursor-not-allowed'
								: ''}"
							multiple
							disabled={!hasPaidAccess || !hasB2BSdkAccess}
						>
							<Combobox.Control>
								<Combobox.Input id="exclude-search" />
								<Combobox.Trigger />
							</Combobox.Control>
							<Portal>
								<Combobox.Positioner>
									<Combobox.Content
										class="bg-surface-100-900 border border-surface-300-700 rounded-lg shadow-lg p-1 w-[min(22rem,calc(100vw-2rem))] max-h-48 overflow-y-auto"
									>
										{#if excludeItems.length > 0}
											{#each excludeItems as item (item.value)}
												<Combobox.Item
													{item}
													class="flex justify-between items-center rounded px-3 py-2 text-sm hover:bg-surface-200-800"
												>
													<div class="min-w-0">
														<Combobox.ItemText>{item.label}</Combobox.ItemText>
													</div>
													<Combobox.ItemIndicator />
												</Combobox.Item>
											{/each}
										{:else}
											<p class="px-3 py-2 text-sm opacity-70">No matching companies</p>
										{/if}
									</Combobox.Content>
								</Combobox.Positioner>
							</Portal>
						</Combobox>
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
						data-intent="search"
						class="btn preset-filled-primary-500 w-full flex items-center justify-center gap-2"
						disabled={!hasPaidAccess || isLoading || isExporting}
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
						type="submit"
						data-intent="email-export"
						formaction="?/emailCsv"
						class="btn preset-tonal-primary w-full flex items-center justify-center gap-2 text-sm"
						disabled={!hasPaidAccess || isLoading || isExporting}
					>
						{#if isExporting}
							<Loader2 size={16} class="animate-spin" />
							Queueing CSV Email...
						{:else}
							<Mail size={16} />
							Email CSV Link
						{/if}
					</button>

					<button
						type="button"
						class="btn preset-tonal w-full flex items-center justify-center gap-2 text-sm"
						onclick={resetFilters}
						disabled={isLoading || isExporting}
					>
						<RotateCcw size={16} />
						Reset Filters
					</button>
				</div>
			</form>

			{#if exportFeedback}
				<p class="text-success-900-100 text-sm text-center">{exportFeedback}</p>
			{/if}

			{#if exportError}
				<p class="text-error-900-100 text-sm text-center">{exportError}</p>
			{/if}

			{#if formError()}
				<p class="text-error-900-100 text-sm text-center">{formError()}</p>
			{/if}

			<!-- Filter Summary -->
			{#if includeDomains.length > 0}
				<div class="text-xs pt-2 border-t border-surface-300-700">
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
		<main class="p-4 overflow-hidden">
			{#if !hasPaidAccess}
				<div class="py-10 relative">
					<div class="absolute inset-0 flex items-start justify-center opacity-10 pt-8">
						<Filter size={120} class="text-surface-500" />
					</div>
					<div class="relative max-w-3xl mx-auto">
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
						<p class="text-lg font-medium mb-3 text-center">Results Area Locked</p>
						<p class="text-sm mb-6 text-center">
							Explore all apps. Discover and filter mobile apps with advanced filters and
							dimensions.
						</p>

						<div class="space-y-6">
							<div>
								<h3 class="font-semibold text-lg mb-2">Key Features</h3>
								<ul class="list-disc list-inside space-y-2 text-sm">
									<li>
										<strong>SDK & Company Filtering:</strong> Find apps using specific SDKs and companies.
									</li>
									<li>
										<strong>Monetization Filters:</strong> Filter by in-app purchases, ads, and detection
										requirements.
									</li>
									<li>
										<strong>Store & Category:</strong> Narrow down by Google Play / Apple App Store and
										category.
									</li>
									<li>
										<strong>Metrics Filtering:</strong> Filter installs, ratings, and monthly installs
										ranges.
									</li>
									<li>
										<strong>Date & Rankings:</strong> Filter by recent updates and current store ranking
										status.
									</li>
								</ul>
							</div>

							<div>
								<h3 class="font-semibold text-lg mb-2">Use Cases</h3>
								<ul class="list-disc list-inside space-y-2 text-sm">
									<li>
										<strong>Sales Teams:</strong> Identify potential customers using competitor SDKs.
									</li>
									<li>
										<strong>Market Research:</strong> Analyze ecosystems by monetization strategy.
									</li>
									<li>
										<strong>Competitive Analysis:</strong> Discover peers in your category and store.
									</li>
									<li>
										<strong>Partnership Discovery:</strong> Find apps likely to benefit from your SDK.
									</li>
								</ul>
							</div>
						</div>

						<div class="mt-6 p-4 rounded-lg border border-surface-300-700 text-center">
							<p class="text-sm mb-3">
								<strong>Access Required:</strong> App Explorer is available to paid subscribers.
							</p>
							<a
								href="/pricing"
								class="btn preset-filled-primary-500 inline-flex items-center gap-2"
							>
								<span class="inline"> View Pricing Plans</span>
							</a>
						</div>
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
					<p class="text-sm">
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
