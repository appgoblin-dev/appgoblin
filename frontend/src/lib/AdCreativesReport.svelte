<script lang="ts">
	import { goto } from '$app/navigation';
	import { LayoutGrid, Lock, RectangleHorizontal, RectangleVertical } from 'lucide-svelte';
	import AdCreativeCard from '$lib/AdCreativeCard.svelte';
	import {
		type AdCreativeCategoryOption,
		adCreativeFormats,
		buildAdCreativesUrl,
		getAdCreativeNetworkLabel
	} from '$lib/ad-creatives';

	interface CreativeCluster {
		vhash: string;
		file_extension: string;
		representative_md5: string;
		top_advertiser_store_id: string | null;
		top_adv_name: string | null;
		top_pub_name: string | null;
		top_host_domain: string | null;
		top_ad_domain_company: string | null;
		top_ad_domain_company_domain: string | null;
		top_host_domain_company: string | null;
		top_host_domain_company_domain: string | null;
		top_ad_domain: string | null;
		top_mmp_name: string | null;
		top_mmp_domain: string | null;
		adv_icon_url: string | null;
		pub_icon_url: string | null;
		company_logo_url_ad: string | null;
		company_logo_url_host: string | null;
		unique_publisher_apps: number;
		unique_advertisers: number;
		unique_adv_names: number;
		unique_pub_names: number;
		unique_ad_networks: number;
		unique_ad_domains: number;
		unique_mmps: number;
		first_seen_at: string;
		last_seen_at: string;
		creative_thumb_url: string;
	}

	interface NetworkFilter {
		key: string;
		label: string;
		filterValue: string;
		logoUrl: string | null;
		count: number;
	}

	interface AdCreativesPageData {
		creativeClusters?: CreativeCluster[];
		networkFilterSourceClusters?: CreativeCluster[];
		categoryOptions?: AdCreativeCategoryOption[];
		selectedCategory?: string;
		selectedFormat?: string;
		searchCompany?: string;
		isSignedIn?: boolean;
		allowAdvancedFilters?: boolean;
		anonymousCreativeLimit?: number;
		signInUrl?: string;
		pageTitle?: string;
		pageDescription?: string;
		pageHeading?: string;
		pageIntro?: string;
		canonicalUrl?: string;
	}

	let { data = {} as AdCreativesPageData }: { data?: AdCreativesPageData } = $props();

	let selectedCategory = $derived(data.selectedCategory || 'overall');
	let selectedFormat = $derived(data.selectedFormat || 'all');
	let selectedSearchCompany = $derived(data.searchCompany || '');
	let categoryOptions = $derived(
		data.categoryOptions || [{ value: 'overall', label: 'Overall (All Apps)' }]
	);
	let creativeClusters = $derived(data.creativeClusters || []);
	let isSignedIn = $derived(Boolean(data.isSignedIn));
	let allowAdvancedFilters = $derived(Boolean(data.allowAdvancedFilters));
	let anonymousCreativeLimit = $derived(data.anonymousCreativeLimit || 8);
	let signInUrl = $derived(data.signInUrl || '/auth/login');
	let networkFilterSourceClusters = $derived(data.networkFilterSourceClusters || creativeClusters);
	let detectedAdvertiserCount = $derived(
		new Set(
			creativeClusters
				.map((cluster) => cluster.top_advertiser_store_id)
				.filter((storeId): storeId is string => Boolean(storeId))
		).size
	);
	let undetectedAdvertiserCount = $derived(
		creativeClusters.filter((cluster) => !cluster.top_advertiser_store_id).length
	);
	let networkFilters = $derived(getNetworkFilters(networkFilterSourceClusters));
	let activeNetworkFilter = $derived(normalizeFilterValue(selectedSearchCompany));
	let orientationLookup = $state<Record<string, 'portrait' | 'landscape'>>({});
	let selectedOrientationFilter = $state<'all' | 'portrait' | 'landscape'>('all');
	let displayedClusters = $derived(
		getDisplayedClusters(creativeClusters, orientationLookup, selectedOrientationFilter)
	);
	let lockedPreviewClusters = $derived(
		!isSignedIn
			? getLockedPreviewClusters(
					networkFilterSourceClusters,
					creativeClusters,
					selectedSearchCompany,
					anonymousCreativeLimit
				)
			: []
	);

	$effect(() => {
		void populateOrientations(creativeClusters);
	});

	function handleFilterChange() {
		const catSelect = document.getElementById('category-select') as HTMLSelectElement | null;
		const fmtSelect = document.getElementById('format-select') as HTMLSelectElement | null;

		const category = catSelect ? catSelect.value : selectedCategory;
		const format = fmtSelect ? fmtSelect.value : selectedFormat;
		const network = selectedSearchCompany;

		goto(buildAdCreativesUrl({ category, format, network }), {
			keepFocus: true,
			noScroll: true
		});
	}

	function handleNetworkFilter(network: string) {
		goto(
			buildAdCreativesUrl({
				category: selectedCategory,
				format: selectedFormat,
				network
			}),
			{
				keepFocus: true,
				noScroll: true
			}
		);
	}

	function clearAllFilters() {
		selectedOrientationFilter = 'all';
		goto(buildAdCreativesUrl({ category: 'overall', format: 'all', network: '' }), {
			keepFocus: true,
			noScroll: true
		});
	}

	function setOrientationFilter(value: 'all' | 'portrait' | 'landscape') {
		if (!allowAdvancedFilters) {
			return;
		}

		selectedOrientationFilter = value;
	}

	function getNetworkButtonClass(isActive: boolean): string {
		return isActive
			? 'border-secondary-700-300 text-secondary-700-300'
			: 'hover:border-secondary-800-200 hover:text-secondary-800-200';
	}

	function getOrientationButtonClass(isActive: boolean): string {
		return isActive
			? 'border border-secondary-700-300 text-secondary-700-300'
			: 'hover:border-secondary-800-200 hover:text-secondary-800-200';
	}

	function getNetworkFilters(clusters: CreativeCluster[]): NetworkFilter[] {
		const networkMap = new Map<string, NetworkFilter>();

		for (const cluster of clusters) {
			const companyDomain =
				cluster.top_ad_domain_company_domain || cluster.top_host_domain_company_domain || null;
			const companyName = cluster.top_ad_domain_company || cluster.top_host_domain_company || null;
			const logoUrl = cluster.company_logo_url_ad || cluster.company_logo_url_host || null;
			const filterValue = getNetworkFilterValue(companyDomain, companyName);

			if (!filterValue) {
				continue;
			}

			const key = normalizeFilterValue(filterValue);
			const existing = networkMap.get(key);
			if (existing) {
				existing.count += 1;
				if (!existing.logoUrl && logoUrl) {
					existing.logoUrl = logoUrl;
				}
				continue;
			}

			networkMap.set(key, {
				key,
				label: companyName || getAdCreativeNetworkLabel(filterValue),
				filterValue,
				logoUrl,
				count: 1
			});
		}

		return Array.from(networkMap.values()).sort(
			(left, right) => right.count - left.count || left.label.localeCompare(right.label)
		);
	}

	async function populateOrientations(clusters: CreativeCluster[]) {
		const unresolved = clusters.filter((cluster) => !orientationLookup[getClusterKey(cluster)]);
		if (unresolved.length === 0) {
			return;
		}

		const nextEntries = await Promise.all(
			unresolved.map(async (cluster) => {
				const orientation = await detectCreativeOrientation(cluster.creative_thumb_url);
				return [getClusterKey(cluster), orientation] as const;
			})
		);

		orientationLookup = {
			...orientationLookup,
			...Object.fromEntries(nextEntries)
		};
	}

	function getDisplayedClusters(
		clusters: CreativeCluster[],
		lookup: Record<string, 'portrait' | 'landscape'>,
		orientationFilter: 'all' | 'portrait' | 'landscape'
	): CreativeCluster[] {
		if (orientationFilter === 'all') {
			return clusters;
		}

		return clusters.filter(
			(cluster) => (lookup[getClusterKey(cluster)] || 'landscape') === orientationFilter
		);
	}

	function getClusterKey(cluster: CreativeCluster): string {
		return `${cluster.representative_md5}:${cluster.file_extension}`;
	}

	function detectCreativeOrientation(url: string): Promise<'portrait' | 'landscape'> {
		return new Promise((resolve) => {
			const image = new Image();
			image.onload = () => {
				resolve(image.naturalHeight > image.naturalWidth ? 'portrait' : 'landscape');
			};
			image.onerror = () => resolve('landscape');
			image.src = url;
		});
	}

	function getNetworkFilterValue(
		companyDomain: string | null,
		companyName: string | null
	): string | null {
		if (companyDomain) {
			return companyDomain.split('.')[0];
		}

		if (!companyName) {
			return null;
		}

		return companyName
			.toLowerCase()
			.replace(/[^a-z0-9]+/g, ' ')
			.trim()
			.replace(/\s+/g, '-');
	}

	function normalizeFilterValue(value: string): string {
		return value.toLowerCase().trim();
	}

	function getClusterNetworkKey(cluster: CreativeCluster): string {
		const filterValue = getNetworkFilterValue(
			cluster.top_ad_domain_company_domain || cluster.top_host_domain_company_domain || null,
			cluster.top_ad_domain_company || cluster.top_host_domain_company || null
		);

		return filterValue ? normalizeFilterValue(filterValue) : '';
	}

	function getClusterOrientation(cluster: CreativeCluster): 'portrait' | 'landscape' {
		return orientationLookup[getClusterKey(cluster)] || 'landscape';
	}

	function getLockedPreviewClusters(
		sourceClusters: CreativeCluster[],
		visibleClusters: CreativeCluster[],
		selectedNetwork: string,
		visibleLimit: number
	): CreativeCluster[] {
		const visibleKeys = new Set(visibleClusters.map(getClusterKey));
		const selectedNetworkKey = normalizeFilterValue(selectedNetwork || '');
		const scopedClusters = sourceClusters.filter((cluster) => {
			if (!selectedNetworkKey) {
				return true;
			}

			return getClusterNetworkKey(cluster) === selectedNetworkKey;
		});

		return scopedClusters
			.filter((cluster) => !visibleKeys.has(getClusterKey(cluster)))
			.slice(0, Math.max(4, Math.min(visibleLimit, 6)));
	}
</script>

<div class="px-4 py-5 md:px-8 lg:px-10 xl:px-12">
	<div class="mx-auto max-w-[1440px] space-y-6">
		<div class="rounded-2xl border p-4 shadow-sm md:p-5">
			<div class="flex flex-col gap-4">
				<div class="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
					<div class="min-w-0">
						<div class="flex flex-col gap-2 xl:flex-row xl:items-end xl:justify-between">
							<div class="min-w-0">
								<h1 class="text-xl font-bold md:text-2xl">
									{data.pageHeading || 'Ad Creative Explorer'}
								</h1>
								<p class="mt-1 max-w-3xl text-sm leading-5 opacity-75">
									{data.pageIntro ||
										'Browse actual videos and images used by top advertisers across ad networks.'}
								</p>
							</div>
						</div>
					</div>
				</div>

				<div class="flex flex-col gap-4 border-t pt-4">
					<div class="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
						<div>
							<h2 class="text-base font-semibold md:text-lg">Filters</h2>
							<p class="mt-0.5 text-sm opacity-70">
								Adjust network, category, format, and orientation without losing the grid.
							</p>
						</div>
						<div class="text-xs opacity-60 md:text-sm">{networkFilters.length} networks shown</div>
					</div>

					<div>
						<div
							class="mb-1.5 block text-[11px] font-medium uppercase tracking-[0.14em] opacity-60"
						>
							Networks
						</div>
						<div class="flex gap-2 overflow-x-auto pb-1">
							<button
								type="button"
								class={`flex min-w-[108px] shrink-0 items-center gap-2 rounded-xl border px-2.5 py-2 text-left text-sm transition ${getNetworkButtonClass(!selectedSearchCompany)}`}
								onclick={() => handleNetworkFilter('')}
							>
								<div
									class="flex h-8 w-8 items-center justify-center rounded-lg text-xs font-semibold"
								>
									All
								</div>
								<div class="min-w-0 flex-1">
									<div class="truncate text-sm font-medium leading-4">All Networks</div>
								</div>
							</button>

							{#each networkFilters as network}
								<button
									type="button"
									class={`flex min-w-[132px] shrink-0 items-center gap-2 rounded-xl border px-2.5 py-2 text-left text-sm transition ${getNetworkButtonClass(activeNetworkFilter === network.key)}`}
									onclick={() => handleNetworkFilter(network.filterValue)}
									aria-pressed={activeNetworkFilter === network.key}
								>
									<div
										class="flex h-10 w-10 shrink-0 items-center justify-center overflow-hidden rounded-lg"
									>
										{#if network.logoUrl}
											<img
												src={`https://media.appgoblin.info/${network.logoUrl}`}
												alt={network.label}
												class="h-9 w-9 rounded object-contain"
												loading="lazy"
											/>
										{:else}
											<span class="text-sm font-semibold"
												>{network.label.slice(0, 2).toUpperCase()}</span
											>
										{/if}
									</div>
									<div class="min-w-0 flex-1">
										<div class="truncate text-sm font-medium leading-4">{network.label}</div>
									</div>
								</button>
							{/each}
						</div>
					</div>

					<div
						class={`rounded-2xl border p-3 md:p-4 ${!allowAdvancedFilters ? 'border-primary-300/60 bg-primary-50/40' : ''}`}
					>
						<div class="mb-3 flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
							<div>
								<div class="flex items-center gap-2 text-sm font-semibold">
									<span>Advanced Filters</span>
								</div>
								{#if !allowAdvancedFilters}
									<p class="mt-1 text-xs text-primary-600 font-medium">
										Available with a free account
									</p>
								{:else}
									<p class="mt-1 text-xs opacity-70">
										Filter by category, format, and orientation.
									</p>
								{/if}
							</div>
							{#if !allowAdvancedFilters}
								<a
									href={signInUrl}
									class="inline-flex items-center gap-2 self-start rounded-full bg-primary-600 px-4 py-1.5 text-xs font-semibold text-white transition hover:bg-primary-700"
								>
									Create free account
								</a>
							{/if}
						</div>

						<div
							class="grid gap-2.5 md:grid-cols-2 xl:grid-cols-[170px_180px_minmax(220px,280px)_auto] xl:items-end"
						>
							<div>
								<label class="label">
									<span
										class="label-text flex items-center gap-1.5 text-[11px] uppercase tracking-[0.14em] opacity-60"
										>Category</span
									>
									<select
										id="category-select"
										class={`select ${!allowAdvancedFilters ? 'cursor-not-allowed opacity-60' : ''}`}
										disabled={!allowAdvancedFilters}
										value={data.selectedCategory || 'overall'}
										onchange={handleFilterChange}
									>
										{#each categoryOptions as cat}
											<option value={cat.value}>{cat.label}</option>
										{/each}
									</select>
								</label>
							</div>

							<div>
								<label class="label">
									<span
										class="label-text flex items-center gap-1.5 text-[11px] uppercase tracking-[0.14em] opacity-60"
										>Format</span
									>
									<select
										id="format-select"
										class={`select ${!allowAdvancedFilters ? 'cursor-not-allowed opacity-60' : ''}`}
										disabled={!allowAdvancedFilters}
										value={data.selectedFormat || 'all'}
										onchange={handleFilterChange}
									>
										{#each adCreativeFormats as fm}
											<option value={fm.value}>{fm.label}</option>
										{/each}
									</select>
								</label>
							</div>

							<div>
								<div
									class="mb-1.5 flex items-center gap-1.5 text-[11px] font-medium uppercase tracking-[0.14em] opacity-60"
								>
									<span>Orientation</span>
								</div>
								<div
									class="flex h-10 w-full rounded-xl border border-surface-300-700 p-1"
									role="radiogroup"
									aria-label="Creative orientation"
								>
									<button
										type="button"
										class={`flex min-w-0 flex-1 items-center justify-center gap-1 rounded-lg px-2 text-sm transition ${getOrientationButtonClass(selectedOrientationFilter === 'all')} ${!allowAdvancedFilters ? 'cursor-not-allowed opacity-55' : ''}`}
										disabled={!allowAdvancedFilters}
										role="radio"
										aria-checked={selectedOrientationFilter === 'all'}
										onclick={() => setOrientationFilter('all')}
									>
										<LayoutGrid size={16} />
										<span>All</span>
									</button>
									<button
										type="button"
										class={`flex min-w-0 flex-1 items-center justify-center gap-1 rounded-lg px-2 text-sm transition ${getOrientationButtonClass(selectedOrientationFilter === 'landscape')} ${!allowAdvancedFilters ? 'cursor-not-allowed opacity-55' : ''}`}
										disabled={!allowAdvancedFilters}
										role="radio"
										aria-checked={selectedOrientationFilter === 'landscape'}
										onclick={() => setOrientationFilter('landscape')}
									>
										<RectangleHorizontal size={16} />
										<span>Landscape</span>
									</button>
									<button
										type="button"
										class={`flex min-w-0 flex-1 items-center justify-center gap-1 rounded-lg px-2 text-sm transition ${getOrientationButtonClass(selectedOrientationFilter === 'portrait')} ${!allowAdvancedFilters ? 'cursor-not-allowed opacity-55' : ''}`}
										disabled={!allowAdvancedFilters}
										role="radio"
										aria-checked={selectedOrientationFilter === 'portrait'}
										onclick={() => setOrientationFilter('portrait')}
									>
										<RectangleVertical size={16} />
										<span>Portrait</span>
									</button>
								</div>
							</div>

							<div class="flex flex-wrap gap-2 lg:justify-end">
								{#if selectedSearchCompany || (allowAdvancedFilters && (selectedCategory !== 'overall' || selectedFormat !== 'all' || selectedOrientationFilter !== 'all'))}
									<button
										type="button"
										class="rounded-full border border-surface-300-700 px-3 py-1.5 text-sm transition"
										onclick={clearAllFilters}
									>
										Clear all
									</button>
								{/if}
							</div>
						</div>
					</div>

					<div class="flex flex-wrap items-center gap-2 text-xs md:text-sm">
						<span class="opacity-60">Current view:</span>
						<span class="rounded-full px-2.5 py-1 md:px-3 md:py-1.5"
							>{creativeClusters.length} creatives</span
						>
						{#if allowAdvancedFilters && selectedCategory !== 'overall'}
							<span class="rounded-full px-2.5 py-1 md:px-3 md:py-1.5"
								>{categoryOptions.find((cat) => cat.value === selectedCategory)?.label ||
									selectedCategory}</span
							>
						{/if}
						{#if allowAdvancedFilters && selectedFormat !== 'all'}
							<span class="rounded-full px-2.5 py-1 md:px-3 md:py-1.5"
								>{adCreativeFormats.find((format) => format.value === selectedFormat)?.label ||
									selectedFormat}</span
							>
						{/if}
						{#if allowAdvancedFilters && selectedOrientationFilter !== 'all'}
							<span class="rounded-full px-2.5 py-1 md:px-3 md:py-1.5"
								>{selectedOrientationFilter === 'portrait'
									? 'Portrait only'
									: 'Landscape only'}</span
							>
						{/if}
						{#if selectedSearchCompany}
							<span class="rounded-full px-2.5 py-1 md:px-3 md:py-1.5"
								>{getAdCreativeNetworkLabel(selectedSearchCompany)}</span
							>
						{/if}
					</div>
				</div>
			</div>

			{#if displayedClusters.length > 0}
				<div class="space-y-6">
					<div
						class="flex flex-col gap-1 border-b pb-2 md:flex-row md:items-end md:justify-between"
					>
						<div>
							<h2 class="text-xl font-semibold">Ad Creatives Feed</h2>
							<p class="mt-1 text-sm opacity-68">
								Portrait and landscape creatives are shown together in one feed.
							</p>
						</div>
						<div class="text-sm opacity-60">{displayedClusters.length} creatives</div>
					</div>

					<div
						class="grid grid-cols-2 gap-x-3 gap-y-4 md:grid-cols-3 md:gap-x-4 md:gap-y-5 lg:grid-cols-4 lg:gap-x-6 2xl:grid-cols-5 2xl:gap-x-8 2xl:gap-y-6"
					>
						{#each displayedClusters as cluster}
							<div class="min-w-0">
								<AdCreativeCard data={cluster} orientation={getClusterOrientation(cluster)} />
							</div>
						{/each}
					</div>

					{#if !isSignedIn && lockedPreviewClusters.length > 0}
						<div class="space-y-3">
							<div class="flex items-center justify-between gap-3">
								<div>
									<h3 class="text-lg font-semibold">
										View all {networkFilterSourceClusters.length} creatives for free
									</h3>
									<p class="mt-1 text-sm opacity-68">
										Create a free account to unlock the full feed and advanced filters.
									</p>
								</div>
								<a
									href={signInUrl}
									class="inline-flex items-center gap-2 rounded-full bg-primary-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-primary-700"
								>
									Create free account
								</a>
							</div>
							<div class="relative">
								<div
									class="grid grid-cols-2 gap-x-3 gap-y-4 opacity-40 blur-[1px] saturate-50 md:grid-cols-3 md:gap-x-4 md:gap-y-5 lg:grid-cols-4 lg:gap-x-6 2xl:grid-cols-5 2xl:gap-x-8 2xl:gap-y-6"
								>
									{#each lockedPreviewClusters as cluster}
										<div class="min-w-0 pointer-events-none select-none">
											<AdCreativeCard data={cluster} orientation={getClusterOrientation(cluster)} />
										</div>
									{/each}
								</div>
								<div
									class="absolute inset-0 flex items-center justify-center rounded-2xl bg-gradient-to-b from-surface-50/10 via-surface-50/55 to-surface-50/85 dark:from-surface-900/10 dark:via-surface-900/50 dark:to-surface-900/80"
								>
									<div
										class="mx-4 max-w-md rounded-2xl border border-primary-300/60 bg-white/88 p-5 text-center shadow-lg backdrop-blur-sm dark:bg-surface-900/88"
									>
										<h4 class="text-lg font-bold text-primary-700">Unlock full access for free</h4>
										<p class="mt-2 text-sm font-medium opacity-80">
											Sign up for a free account to view the complete creative library, unlock
											advanced filters, and more.
										</p>
										<div class="mt-5 flex justify-center gap-3">
											<a
												href={signInUrl}
												class="inline-flex items-center justify-center rounded-full bg-primary-600 px-6 py-2.5 text-sm font-bold text-white transition hover:bg-primary-700"
											>
												Create Free Account
											</a>
										</div>
									</div>
								</div>
							</div>
						</div>
					{/if}
				</div>
			{:else}
				<div class="rounded-2xl border-2 border-dashed py-16 text-center">
					<h3 class="text-xl font-medium opacity-70">No ad creatives found</h3>
					<p class="mt-2 text-sm opacity-60">
						Try selecting a different category or adjusting filters.
					</p>
				</div>
			{/if}
		</div>
	</div>
</div>
