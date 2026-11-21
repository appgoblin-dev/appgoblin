<script lang="ts">
	import type { CompanyFullDetails, CompanyOverviewScope } from '../../../../types';

	type CategoryItem = {
		group: string;
		category: string;
		value: number;
	};

	import CompanyCategoryControls from '#lib/CompanyCategoryControls.svelte';
	import CompanyCountryAppPie from '#lib/CompanyCountryAppPie.svelte';
	import TotalsBox from '#lib/TotalsBox.svelte';
	import ApiTotalsBox from '#lib/ApiTotalsBox.svelte';
	import CompanyCategoryPie from '#lib/CompanyCategoryPie.svelte';
	import AdsTxtTotalsBox from '#lib/AdsTxtTotalsBox.svelte';
	import CompanyTableGrid from '#lib/CompanyTableGrid.svelte';
	import HierarchyTree from '#lib/HierarchyTree.svelte';
	import WhiteCard from '#lib/WhiteCard.svelte';
	import CompanySectionLink from '#lib/utils/CompanySectionLink.svelte';
	import { companySectionHasData } from '#lib/utils/companySectionAvailability.js';
	import { page } from '$app/state';
	import type { CompanyLayoutDetails } from '../../../../types';
	import ApiDataNote from '#lib/ApiDataNote.svelte';
	interface Props {
		data: CompanyFullDetails;
	}

	let { data }: Props = $props();
	let companyName = $derived(
		data.companyTree.is_secondary_domain
			? data.companyTree.queried_domain
			: data.companyTree.company_name ||
					data.companyTree.company_domain ||
					data.companyTree.queried_domain
	);
	let hasHigherLevelParent = $derived(
		Boolean(
			data.companyTree.parent &&
			data.companyTree.parent.company_domain !== data.companyTree.company_domain
		)
	);
	let hasHierarchyContext = $derived(
		Boolean(data.companyTree.company_domain || data.companyTree.parent)
	);
	let queriedIsMappedCompany = $derived(
		data.companyTree.queried_domain === data.companyTree.company_domain
	);
	let associatedDomains = $derived(data.companyTree?.domains ?? []);
	type OverviewTab = 'domain' | 'parent';
	let selectedOverview = $derived<OverviewTab>(
		data.companyDetails.parent_overview ? 'parent' : 'domain'
	);
	let fallbackOverview = $derived({
		categories: data.companyDetails.categories,
		adstxt_ad_domain_overview: data.companyDetails.adstxt_ad_domain_overview,
		adstxt_publishers_overview: data.companyDetails.adstxt_publishers_overview,
		trends_summary: data.companyDetails.trends_summary ?? null
	} as CompanyOverviewScope);
	let domainOverview = $derived(data.companyDetails.domain_overview ?? fallbackOverview);
	let parentOverview = $derived(data.companyDetails.parent_overview ?? null);
	let categoryControlOverview = $derived(parentOverview ?? domainOverview);
	let activeOverview = $derived(
		selectedOverview === 'parent' ? (parentOverview ?? domainOverview) : domainOverview
	);
	// Trends summary is only computed for the domain scope in the backend.
	// When parent scope is selected, fall back to the domain-level trends summary.
	let activeTrendsSummary = $derived(
		activeOverview.trends_summary ?? data.companyDetails.trends_summary ?? null
	);
	let activeCategoryPromise = $derived(
		selectedOverview === 'parent' && data.parentAppCategories
			? data.parentAppCategories
			: data.companyAppCategories
	);

	type GroupMode = 'all' | 'games' | 'apps';
	let androidGroupMode = $state<GroupMode>('all');
	let iosGroupMode = $state<GroupMode>('all');

	const numberFormatter = new Intl.NumberFormat('en-US');
	function formatCount(value: number | null | undefined): string {
		return numberFormatter.format(Math.max(0, Math.round(value ?? 0)));
	}

	function joinWithAnd(items: string[]): string {
		if (items.length === 0) return '';
		if (items.length === 1) return items[0];
		if (items.length === 2) return `${items[0]} and ${items[1]}`;
		return `${items.slice(0, -1).join(', ')}, and ${items[items.length - 1]}`;
	}

	// Human-readable label for the company's primary classification (ad network, analytics, etc.).
	const companyTypeLabels: Record<string, string> = {
		'ad-networks': 'ad network',
		'ad-network': 'ad network',
		attribution: 'attribution provider',
		analytics: 'analytics provider',
		mediation: 'mediation platform',
		'product-analytics': 'product analytics provider'
	};
	let primaryCompanyType = $derived(data.companyDetails?.company_types?.[0] ?? null);
	let companyTypeLabel = $derived(
		primaryCompanyType
			? (companyTypeLabels[primaryCompanyType] ??
					primaryCompanyType.replace(/-/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase()))
			: null
	);
	let isAdNetwork = $derived(
		(data.companyDetails?.company_types ?? []).some(
			(t) => t === 'ad-networks' || t === 'ad-network'
		)
	);

	let overviewStats = $derived(activeOverview.categories.all);
	let totalApps = $derived(overviewStats?.total_apps ?? 0);
	let sdkApps = $derived(overviewStats?.sdk_total_apps ?? 0);
	let apiApps = $derived(overviewStats?.api_total_apps ?? 0);
	let adstxtApps = $derived(
		(overviewStats?.adstxt_direct_ios_total_apps ?? 0) +
			(overviewStats?.adstxt_direct_android_total_apps ?? 0) +
			(overviewStats?.adstxt_reseller_ios_total_apps ?? 0) +
			(overviewStats?.adstxt_reseller_android_total_apps ?? 0)
	);

	// Pull a few notable client app names from the top Android/iOS lists for richer, SEO-friendly copy.
	let topApps = $derived(typeof data.companyTopApps === 'string' ? null : data.companyTopApps);
	let notableApps = $derived.by(() => {
		if (!topApps) return [] as string[];
		const androidApps =
			(topApps as { android?: { apps?: { app_name?: string }[] } }).android?.apps ?? [];
		const iosApps = (topApps as { ios?: { apps?: { app_name?: string }[] } }).ios?.apps ?? [];
		const names: string[] = [];
		const seen = new Set<string>();
		for (const app of [...androidApps, ...iosApps]) {
			const name = app?.app_name?.trim();
			if (name && !seen.has(name.toLowerCase())) {
				seen.add(name.toLowerCase());
				names.push(name);
			}
			if (names.length >= 3) break;
		}
		return names;
	});

	let subject = $derived(
		companyTypeLabel ? `${companyName}, a mobile ${companyTypeLabel},` : companyName
	);
	let signalCounts = $derived(
		[
			{ slug: 'sdks' as const, value: sdkApps, label: 'apps with detected SDKs' },
			{ slug: 'api-apps' as const, value: apiApps, label: 'apps making API calls' },
			{ slug: 'app-adstxt' as const, value: adstxtApps, label: 'app-ads.txt listings' }
		].filter((signal) => signal.value > 0)
	);
	const relatedSections = [
		{ slug: 'creatives', label: 'creatives' },
		{ slug: 'trends', label: 'trends' },
		{ slug: 'mediation', label: 'mediation adapters' },
		{ slug: 'mediation-partners', label: 'mediation partners' },
		{ slug: 'apps-added', label: 'SDK/API additions' },
		{ slug: 'apps-lost', label: 'SDK/API losses' },
		{ slug: 'apps-added-adstxt', label: 'app-ads.txt additions' },
		{ slug: 'apps-lost-adstxt', label: 'app-ads.txt losses' },
		{ slug: 'data-exports', label: 'data exports' }
	] as const;
	let companyLayout = $derived(page.data as CompanyLayoutDetails);
	let availableSections = $derived(
		relatedSections.filter((section) =>
			companySectionHasData(
				section.slug,
				companyLayout.tabIndicators,
				companyLayout.mediationPartners?.length
			)
		)
	);
</script>

<div class="grid grid-cols-1 md:grid-cols-3 gap-4 md:gap-6 mb-6">
	<div class="md:col-span-2 space-y-2">
		<p class="text-base">
			{#if totalApps > 0}
				{subject} is tied to {formatCount(totalApps)} mobile apps{#if signalCounts.length > 0},
					including
					{#each signalCounts as signal, i (signal.slug)}
						{#if i > 0}{i === signalCounts.length - 1
								? signalCounts.length > 2
									? ', and '
									: ' and '
								: ', '}{/if}<CompanySectionLink slug={signal.slug}
							>{formatCount(signal.value)} {signal.label}</CompanySectionLink
						>
					{/each}{/if}.
			{:else}
				AppGoblin tracks {companyName} across <CompanySectionLink slug="sdks"
					>SDKs</CompanySectionLink
				>,
				<CompanySectionLink slug="api-apps">API calls</CompanySectionLink>, and
				<CompanySectionLink slug="app-adstxt">app-ads.txt records</CompanySectionLink>.
			{/if}
			{#if notableApps.length > 0}
				Top apps using {companyName} include {joinWithAnd(notableApps)}.
			{/if}
		</p>
		{#if availableSections.length > 0}
			<p class="text-base">
				Explore {#each availableSections as section, i (section.slug)}{#if i > 0}{i ===
						availableSections.length - 1
							? availableSections.length > 2
								? ', and '
								: ' and '
							: ', '}{/if}<CompanySectionLink slug={section.slug}
						>{section.label}</CompanySectionLink
					>{/each}.
			</p>
		{/if}
	</div>
	<div class="md:row-span-2">
		<WhiteCard>
			{#snippet title()}
				<span>{companyName}'s Related Entities</span>
			{/snippet}
			<div class="p-2">
				{#if hasHierarchyContext}
					<HierarchyTree
						companyTree={data.companyTree}
						{hasHigherLevelParent}
						{queriedIsMappedCompany}
						{associatedDomains}
						showTruncated={true}
					/>
				{/if}

				{#if typeof data.companyTree == 'string'}
					<p class="text-red-500 text-center">Failed to load company tree.</p>
				{:else}
					<!-- REGULAR COMPANY (no child or parent companies) -->
				{/if}
			</div>
		</WhiteCard>
	</div>
	{#if !data.companyTree.is_secondary_domain}
		<div class="md:col-span-1">
			<WhiteCard>
				{#snippet title()}
					<span>{companyName}'s Android Apps by Category</span>
				{/snippet}
				<div>
					{#await activeCategoryPromise}
						<span class="text-lg">Loading...</span>
					{:then myPieData}
						{#if myPieData && 'error' in myPieData}
							<p class="text-red-500 text-center">Failed to load categories.</p>
						{:else if myPieData}
							<CompanyCategoryPie
								plotData={myPieData.android as CategoryItem[]}
								storeLabel="Google Play"
								bind:groupMode={androidGroupMode}
							/>
						{/if}
					{:catch error}
						<p class="text-red-500 text-center">{error.message}</p>
					{/await}
				</div>
			</WhiteCard>
		</div>
		<div class="md:col-span-1">
			<WhiteCard>
				{#snippet title()}
					<span>{companyName}'s iOS Apps by Category</span>
				{/snippet}
				<div>
					{#await activeCategoryPromise}
						<span class="text-lg">Loading...</span>
					{:then myPieData}
						{#if myPieData && 'error' in myPieData}
							<p class="text-red-500 text-center">Failed to load categories.</p>
						{:else if myPieData}
							<CompanyCategoryPie
								plotData={myPieData.ios as CategoryItem[]}
								storeLabel="Apple App Store"
								bind:groupMode={iosGroupMode}
							/>
						{/if}
					{:catch error}
						<p class="text-red-500 text-center">{error.message}</p>
					{/await}
				</div>
			</WhiteCard>
		</div>
		{#if data.companyCountryApps?.android?.length || data.companyCountryApps?.ios?.length}
			<div class="md:col-span-1">
				<WhiteCard>
					{#snippet title()}
						<span>{companyName}'s Android Apps by Country</span>
					{/snippet}
					<div>
						{#if data.companyCountryApps?.android?.length}
							<CompanyCountryAppPie
								plotData={data.companyCountryApps.android}
								storeLabel="Google Play"
							/>
						{:else}
							<p class="text-center text-sm text-gray-600">No Android data.</p>
						{/if}
					</div>
				</WhiteCard>
			</div>
			<div class="md:col-span-1">
				<WhiteCard>
					{#snippet title()}
						<span>{companyName}'s iOS Apps by Country</span>
					{/snippet}
					<div>
						{#if data.companyCountryApps?.ios?.length}
							<CompanyCountryAppPie
								plotData={data.companyCountryApps.ios}
								storeLabel="Apple App Store"
							/>
						{:else}
							<p class="text-center text-sm text-gray-600">No iOS data.</p>
						{/if}
					</div>
				</WhiteCard>
			</div>
		{/if}
	{/if}
</div>

<div class="mb-4 md:mb-6">
	<WhiteCard>
		{#snippet title()}
			<span>{companyName} Apps Overview</span>
		{/snippet}
		<div class="px-4 pt-4 flex flex-col gap-3 lg:flex-row lg:items-end lg:gap-6">
			{#if parentOverview}
				<div>
					<span
						class="mb-1 flex items-center gap-1.5 text-[11px] uppercase tracking-[0.14em] opacity-60"
						>Data Scope</span
					>
					<div
						class="inline-flex rounded-md border border-surface-300-700 p-1"
						role="radiogroup"
						aria-label="Data scope"
					>
						<button
							type="button"
							title="Roll up all subsidiaries and child domains under this company"
							class={`flex items-center justify-center gap-1 rounded-md px-2.5 py-1 text-sm transition ${selectedOverview === 'parent' ? 'border border-secondary-700-300 text-secondary-700-300' : 'border border-transparent hover:border-secondary-800-200 hover:text-secondary-800-200'}`}
							role="radio"
							aria-checked={selectedOverview === 'parent'}
							onclick={() => (selectedOverview = 'parent')}
						>
							Parent Co.
						</button>
						<button
							type="button"
							title="Limit to this exact domain only, excluding subsidiaries"
							class={`flex items-center justify-center gap-1 rounded-md px-2.5 py-1 text-sm transition ${selectedOverview === 'domain' ? 'border border-secondary-700-300 text-secondary-700-300' : 'border border-transparent hover:border-secondary-800-200 hover:text-secondary-800-200'}`}
							role="radio"
							aria-checked={selectedOverview === 'domain'}
							onclick={() => (selectedOverview = 'domain')}
						>
							Exact Domain
						</button>
					</div>
				</div>
			{/if}
			<CompanyCategoryControls
				overview={categoryControlOverview}
				compact={true}
				hasB2BAccess={data.hasB2BSdkAccess}
			/>
		</div>
		{#if data.companyTree.is_secondary_domain}
			<p class="px-4 pt-4 text-sm text-gray-600">
				This queried domain maps to {data.companyTree.company_name ||
					data.companyTree.company_domain}.
				{#if hasHigherLevelParent}
					The larger parent company is {data.companyTree.parent?.company_name ||
						data.companyTree.parent?.company_domain}.
				{/if}
			</p>
		{/if}
		<div class="grid gap-4 p-4 lg:grid-cols-2">
			<div class="rounded border border-surface-200-800/70">
				<TotalsBox
					{companyName}
					myTotals={activeOverview.categories.all}
					myType={{ name: 'All Companies & Domains', url_slug: 'all-companies' }}
					hideAdstxtApps={true}
					isSecondaryDomain={data.companyTree.is_secondary_domain}
					trendsSummary={activeTrendsSummary}
				/>
			</div>
			<div class="rounded border border-surface-200-800/70">
				<ApiTotalsBox
					{companyName}
					myTotals={activeOverview.categories.all}
					trendsSummary={activeTrendsSummary}
				/>
			</div>
			{#if isAdNetwork}
				<div class="rounded border border-surface-200-800/70">
					<AdsTxtTotalsBox
						myTotals={activeOverview.adstxt_ad_domain_overview}
						trendsSummary={activeTrendsSummary}
						showReseller={false}
					/>
				</div>
				<div class="rounded border border-surface-200-800/70">
					<AdsTxtTotalsBox myTotals={activeOverview.adstxt_ad_domain_overview} showDirect={false} />
				</div>
			{/if}
		</div>
	</WhiteCard>
</div>

{#if typeof data.companyTopApps == 'string'}
	Failed to load company's apps.
{:else}
	<CompanyTableGrid
		tableData={data.companyTopApps}
		companyName={companyName || ''}
		previewMode={!data.hasB2BSdkAccess}
	/>
{/if}
{#if data.companyTree && (associatedDomains.length > 0 || data.companyTree.children.length > 0)}
	<section class="mt-6">
		<h3 class="text-xl font-semibold mb-2">Full Hierarchy</h3>
		<p class="text-sm text-gray-600 mb-3">
			Complete company ownership structure and all associated domains.
		</p>
		<HierarchyTree
			companyTree={data.companyTree}
			{hasHigherLevelParent}
			{queriedIsMappedCompany}
			{associatedDomains}
			showTruncated={false}
		/>
	</section>
{/if}
<ApiDataNote endpoint={'/api/v1/companies/{company_domain}'} />
