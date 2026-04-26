<script lang="ts">
	import type { CompaniesOverview } from '../../../types';
	import CompaniesOverviewTable from '$lib/CompaniesOverviewTable.svelte';
	import CompaniesTableGrid from '$lib/CompaniesTableGrid.svelte';
	interface Props {
		data: CompaniesOverview;
	}

	let { data }: Props = $props();

	const title = 'Top App Ad Networks, Dev Tools & Analytics for Apps';
	const description =
		'See which apps use which app ad networks, analytics and trackers. Competitor analysis based on API, SDK and trackers used on all apps for mobile app companies.';
	const canonicalUrl = 'https://appgoblin.info/companies';

	let topCompanies = $derived(
		typeof data.companiesOverview === 'string'
			? []
			: (data.companiesOverview?.companies_overview ?? []).slice(0, 10)
	);

	let structuredData = $derived({
		'@context': 'https://schema.org',
		'@type': 'CollectionPage',
		name: title,
		description,
		url: canonicalUrl,
		inLanguage: 'en',
		isPartOf: {
			'@type': 'WebSite',
			name: 'AppGoblin',
			url: 'https://appgoblin.info'
		},
		mainEntity: {
			'@type': 'ItemList',
			itemListOrder: 'https://schema.org/ItemListOrderDescending',
			numberOfItems: topCompanies.length,
			itemListElement: topCompanies.map((company: any, index: number) => ({
				'@type': 'ListItem',
				position: index + 1,
				name: company.company_name || company.company_domain || 'Company',
				url: company.company_domain
					? `https://appgoblin.info/companies/${company.company_domain}`
					: canonicalUrl
			}))
		}
	});
</script>

<svelte:head>
	<title>{title}</title>
	<meta name="description" content={description} />
	<meta
		name="keywords"
		content="mobile, development tools, ad networks, data trackers, MMPs, programmatic networks, app-ads.txt, mobile advertising, ad tech analytics, app marketing, AppGoblin"
	/>
	<meta property="og:title" content={title} />
	<meta property="og:description" content={description} />
	<meta name="twitter:title" content={title} />
	<meta name="twitter:description" content={description} />
	<meta property="og:image" content="https://appgoblin.info/adtech-companies-banner.png" />
	<meta property="og:url" content={canonicalUrl} />
	<meta property="og:type" content="website" />
	<meta name="twitter:card" content="summary_large_image" />
	<meta name="twitter:image" content="https://appgoblin.info/adtech-companies-banner.png" />
	<link rel="canonical" href={canonicalUrl} />
	<meta name="robots" content="index, follow" />
	{@html `<script type="application/ld+json">${JSON.stringify(structuredData)}</script>`}
</svelte:head>

{#if typeof data.companiesOverview == 'string'}
	<p class="text-red-500 text-center">Failed to load companies details.</p>
{:else if data.companiesOverview && data.companiesOverview.categories}
	<p class="text-sm mb-4">
		Explore verified ad networks, analytics platforms, mediation providers, and developer tooling
		across millions of mobile apps. This view is updated with SDK, API, and app-ads.txt intelligence
		to help researchers, growth teams, and fraud analysts compare market presence and technical
		footprint.
	</p>
	<CompaniesTableGrid>
		{#snippet mainTable()}
			{#if data.companiesOverview && data.companiesOverview.companies_overview.length > 0}
				<CompaniesOverviewTable data={data.companiesOverview.companies_overview} />
			{/if}
		{/snippet}
	</CompaniesTableGrid>
{/if}
