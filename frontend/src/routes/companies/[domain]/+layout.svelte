<script lang="ts">
	import { page } from '$app/state';
	import type { CompanyLayoutDetails, CompanyTypes } from '../../../types';

	import ExternalLink from '$lib/ExternalLink.svelte';
	import CompanyButton from '$lib/CompanyButton.svelte';
	import FollowToggleButton from '$lib/components/follows/FollowToggleButton.svelte';
	import CompanyTypesTabs from '$lib/utils/CompanyTypesTabs.svelte';

	let { children, data }: { children: any; data: CompanyLayoutDetails } = $props();
	const domain = page.params.domain ?? '';

	let companyTypesData = $derived((page.data as { companyTypes?: CompanyTypes }).companyTypes);

	let categoryName = $derived(getAppCategory(page.params.category || ''));

	function getAppCategory(category: string) {
		if (category) {
			return category
				.split('_')
				.map((c) => c.charAt(0).toUpperCase() + c.slice(1))
				.join(' ');
		} else {
			return 'All ';
		}
	}

	function getSectionSlug(pathname: string) {
		if (pathname.includes('/app-adstxt/publisher/')) return 'app-adstxt-publisher';
		if (pathname.includes('/app-adstxt')) return 'app-adstxt';
		if (pathname.includes('/creatives')) return 'creatives';
		if (pathname.includes('/data-exports')) return 'data-exports';
		if (pathname.includes('/mediation')) return 'mediation';
		if (pathname.includes('/sdks')) return 'sdks';
		return 'overview';
	}

	function isSectionTabActive(tabSlug: string): boolean {
		if (tabSlug === 'app-adstxt') {
			return sectionSlug === 'app-adstxt' || sectionSlug === 'app-adstxt-publisher';
		}
		return sectionSlug === tabSlug;
	}

	function sectionTabClass(tabSlug: string): string {
		const selectedClass =
			'px-2 md:px-4 py-2 border-t-1 border-r-1 border-l-1 bg-secondary-100-900 border-secondary-100-900 rounded-t-md relative';
		const unselectedClass = 'px-2 md:px-4 py-2 border-b-1 border-surface-800-200 ';
		return isSectionTabActive(tabSlug) ? selectedClass : unselectedClass;
	}

	let sectionSlug = $derived(getSectionSlug(page.url.pathname));
	let companyDomain = $derived(
		data.companyTree?.queried_domain || data.companyTree?.company_domain || domain
	);
	let showMediationTab = $derived(Boolean(data.companyDetails?.mediation_adapters));
	let showCreativesTab = $derived(
		Boolean(
			data.companyDetails?.company_types?.some((companyType) => companyType === 'ad-networks')
		)
	);
	let companyDisplayName = $derived(
		data.companyTree?.company_name ||
			data.companyTree?.company_domain ||
			data.companyTree?.queried_domain ||
			domain
	);

	let hasHigherLevelParent = $derived(
		Boolean(
			data.companyTree?.is_secondary_domain &&
			data.companyTree?.parent &&
			data.companyTree.parent.company_domain !== data.companyTree.company_domain
		)
	);
	let selectedCategoryName = $derived(
		categoryName && categoryName.trim() ? categoryName : 'All Apps'
	);
	let categoryContext = $derived(
		selectedCategoryName === 'All ' || selectedCategoryName === 'All Apps'
			? 'all app categories'
			: `${selectedCategoryName} apps`
	);

	let pageTitle = $derived.by(() => {
		switch (sectionSlug) {
			case 'sdks':
				return `${companyDisplayName} SDK Intelligence for ${categoryContext} | AppGoblin`;
			case 'mediation':
				return `${companyDisplayName} Mediation Adapter Coverage | AppGoblin`;
			case 'creatives':
				return `${companyDisplayName} Ad Creatives and Campaign Signals | AppGoblin`;
			case 'app-adstxt':
				return `${companyDisplayName} App-Ads.txt Direct and Reseller IDs | AppGoblin`;
			case 'app-adstxt-publisher':
				return `${companyDisplayName} App-Ads.txt Publisher ID Detail | AppGoblin`;
			case 'data-exports':
				return `${companyDisplayName} Mobile Intelligence Data Exports | AppGoblin`;
			default:
				return `${companyDisplayName} Mobile SDK, API, and App-Ads.txt Intelligence | AppGoblin`;
		}
	});

	let pageDescription = $derived.by(() => {
		switch (sectionSlug) {
			case 'sdks':
				return `Review the SDK footprint for ${companyDisplayName} across ${categoryContext}, including adtech, analytics, and developer tooling integrations.`;
			case 'mediation':
				return `Analyze mediation adapters used by ${companyDisplayName} and evaluate monetization stack coverage across real mobile apps.`;
			case 'creatives':
				return `Browse recent creatives linked to ${companyDisplayName} to monitor ad campaign activity, placement signals, and market behavior.`;
			case 'app-adstxt':
				return `Track app-ads.txt direct and reseller publisher IDs tied to ${companyDisplayName}, mapped to real app store IDs and updated daily.`;
			case 'app-adstxt-publisher':
				return `Inspect publisher-level app-ads.txt records connected to ${companyDisplayName}, including direct and reseller relationships across apps.`;
			case 'data-exports':
				return `Access structured data exports for ${companyDisplayName}, including app-ads.txt and SDK/API traffic intelligence for paid members.`;
			default:
				return `Explore ${companyDisplayName} across ${categoryContext} with app-level intelligence for SDK usage, API behavior, and app-ads.txt relationships.`;
		}
	});

	let breadcrumbList = $derived.by(() => {
		const crumbs = [
			{ name: 'Home', item: 'https://appgoblin.info/' },
			{ name: 'Companies', item: 'https://appgoblin.info/companies' },
			{
				name: companyDisplayName,
				item: `https://appgoblin.info/companies/${companyDomain}`
			}
		];

		if (sectionSlug !== 'overview') {
			crumbs.push({ name: sectionSlug.replace(/-/g, ' '), item: page.url.href });
		}

		return crumbs.map((crumb, index) => ({
			'@type': 'ListItem',
			position: index + 1,
			name: crumb.name,
			item: crumb.item
		}));
	});

	let structuredData = $derived.by(() => {
		const companyUrl = `https://appgoblin.info/companies/${companyDomain}`;
		const logoUrl = data.companyTree?.company_logo_url
			? `https://media.appgoblin.info/${data.companyTree.company_logo_url}`
			: data.companyTree?.parent?.company_logo_url
				? `https://media.appgoblin.info/${data.companyTree.parent.company_logo_url}`
				: 'https://appgoblin.info/default_company_logo.png';

		return {
			'@context': 'https://schema.org',
			'@graph': [
				{
					'@type': 'WebPage',
					name: pageTitle,
					description: pageDescription,
					url: page.url.href,
					inLanguage: 'en',
					isPartOf: {
						'@type': 'WebSite',
						name: 'AppGoblin',
						url: 'https://appgoblin.info'
					},
					about: {
						'@id': `${companyUrl}#organization`
					}
				},
				{
					'@type': 'Organization',
					'@id': `${companyUrl}#organization`,
					name: companyDisplayName,
					url: companyUrl,
					logo: logoUrl
				},
				{
					'@type': 'BreadcrumbList',
					itemListElement: breadcrumbList
				}
			]
		};
	});

	let titleClass = 'h1 text-2xl md:text-3xl font-bold ';
	let titleSecondaryClass = 'text-xl font-bold  mr-2';
	let titleDividerClass = 'md:h-8 w-px bg-gray-300 mx-2';
</script>

<svelte:head>
	<title>{pageTitle}</title>
	<meta name="description" content={pageDescription} />
	<meta
		name="keywords"
		content={`${domain}, ${selectedCategoryName}, adtech, advertising network, data tracking, mobile measurement, programmatic advertising, app-ads.txt, mobile advertising, ad tech analytics, AppGoblin`}
	/>
	<meta property="og:title" content={pageTitle} />
	<meta property="og:description" content={pageDescription} />
	<meta name="twitter:title" content={pageTitle} />
	<meta name="twitter:description" content={pageDescription} />

	<meta property="og:image" content="https://appgoblin.info/goblin_purple_hat_250.png" />
	<meta property="og:url" content={page.url.href} />
	<meta property="og:type" content="website" />
	<meta name="twitter:card" content="summary_large_image" />
	<meta name="twitter:image" content="https://appgoblin.info/goblin_purple_hat_250.png" />
	<link rel="canonical" href={page.url.href} />
	<meta name="robots" content="index, follow" />
	{@html `<script type="application/ld+json">${JSON.stringify(structuredData)}</script>`}
</svelte:head>

{#if !page.url.pathname.includes('adstxt') && companyTypesData && companyTypesData.types.length > 0}
	<CompanyTypesTabs companyTypes={companyTypesData} />
{/if}

<div class="flex flex-wrap gap-2 mb-4 border-b border-surface-200-800 pb-2">
	<a href={`/companies/${companyDomain}`} class={sectionTabClass('overview')}>
		{companyDisplayName} Apps Overview
	</a>
	{#if showMediationTab}
		<a href={`/companies/${companyDomain}/mediation`} class={sectionTabClass('mediation')}>
			{companyDisplayName} Mediation Adapters
		</a>
	{/if}
	{#if showCreativesTab}
		<a href={`/companies/${companyDomain}/creatives`} class={sectionTabClass('creatives')}
			>{companyDisplayName} Creatives
		</a>
	{/if}
	<a href={`/companies/${companyDomain}/sdks`} class={sectionTabClass('sdks')}>
		{companyDisplayName} SDKs
	</a>
	<a href={`/companies/${companyDomain}/app-adstxt`} class={sectionTabClass('app-adstxt')}
		>{companyDisplayName} App-ads.txt
	</a>
	<a href={`/companies/${companyDomain}/data-exports`} class={sectionTabClass('data-exports')}>
		{companyDisplayName} Data Exports
	</a>
</div>

<div class="flex items-center mb-2">
	{#await data.companyTree}
		<span class="text-lg">Loading...</span>
	{:then myTree}
		{#if typeof myTree == 'string'}
			<h1 class={titleClass}>{domain}</h1>
			<p class="text-red-500">Failed to load company tree.</p>
		{:else if myTree}
			<div class="flex flex-col md:flex-row items-left md:items-center">
				{#if page.url.pathname.includes('adstxt/publisher') && myTree.parent}
					<h1 class={titleClass}>
						<a href={`/companies/${myTree.parent.company_domain}`}
							>{myTree.parent.company_name || myTree.parent.company_domain}</a
						>
					</h1>
				{:else if myTree.company_domain || myTree.queried_domain}
					{#if myTree.company_logo_url}
						<img
							src="https://media.appgoblin.info/{myTree.company_logo_url}"
							alt={myTree.company_logo_url}
							class="w-20 h-20 rounded-sm mr-2 md:mr-8"
						/>
					{:else if myTree.parent?.company_logo_url}
						<img
							src="https://media.appgoblin.info/{myTree.parent.company_logo_url}"
							alt={myTree.parent.company_logo_url}
							class="w-20 h-20 rounded-sm mr-2 md:mr-8"
						/>
					{:else}
						<img
							src="/default_company_logo.png"
							alt="Default Company Logo"
							class="w-20 h-20 rounded-sm mr-2 md:mr-8"
						/>
					{/if}

					{#if !myTree.parent && !myTree.is_secondary_domain && !myTree.is_orphan}
						<!-- IS PARENT COMPANY -->
						<h1 class={titleClass}>
							{myTree.company_name || myTree.company_domain || myTree.queried_domain}, App Category:
							{categoryName}
						</h1>
						<div class={titleDividerClass}></div>
						<ExternalLink domain={myTree.company_domain || myTree.queried_domain} />
					{:else if myTree.is_secondary_domain}
						<!-- IS SUB DOMAIN ONLY -->
						<h1 class={titleClass}>{myTree.queried_domain} / {categoryName}</h1>
						<div class={titleDividerClass}></div>
						<ExternalLink domain={myTree.queried_domain} />
						<div class={titleDividerClass}></div>
						<span class="flex row items-center">
							<h2 class={titleSecondaryClass}>Company:</h2>
							<CompanyButton
								companyName={myTree.company_name || undefined}
								companyDomain={myTree.company_domain || myTree.queried_domain}
								companyLogoUrl={myTree.company_logo_url || undefined}
							/>
						</span>
						{#if hasHigherLevelParent && myTree.parent}
							<div class={titleDividerClass}></div>
							<span class="flex row">
								<h2 class={titleSecondaryClass}>Parent:</h2>
								<CompanyButton
									companyName={myTree.parent.company_name}
									companyDomain={myTree.parent.company_domain}
									companyLogoUrl={myTree.parent.company_logo_url || undefined}
								/>
							</span>
						{/if}
					{:else}
						<!-- REGULAR COMPANY  -->
						<h1 class={titleClass}>
							{myTree.company_name || myTree.company_domain || myTree.queried_domain} / {categoryName}
						</h1>
						<div class={titleDividerClass}></div>
						<ExternalLink domain={myTree.company_domain || myTree.queried_domain} />
						{#if myTree.parent}
							<div class={titleDividerClass}></div>
							<!-- HAS PARENT COMPANY -->
							<span class="flex row">
								<h2 class={titleSecondaryClass}>Parent Company:</h2>
								<CompanyButton
									companyName={myTree.parent.company_name}
									companyDomain={myTree.parent.company_domain}
									companyLogoUrl={myTree.parent.company_logo_url || undefined}
								/>
							</span>
						{/if}
					{/if}
				{/if}
			</div>
			{#if data.companyLookup?.company_id}
				<div class="mt-2 md:mt-0 md:ml-4">
					<FollowToggleButton
						entity="company"
						label="Company"
						companyId={data.companyLookup.company_id}
						initialFollowing={Boolean(data.isFollowingCompany)}
					/>
				</div>
			{/if}
		{/if}
	{:catch error}
		<p class="text-red-500">{error.message}</p>
	{/await}
</div>

<div class="space-y-4 md:space-y-8">
	{@render children?.()}
</div>
