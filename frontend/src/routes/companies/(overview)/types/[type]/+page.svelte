<script lang="ts">
	import { page } from '$app/state';
	import CompaniesOverviewTable from '#lib/CompaniesOverviewTable.svelte';
	import CompaniesTableGrid from '#lib/CompaniesTableGrid.svelte';
	import WhiteCard from '#lib/WhiteCard.svelte';
	import CompanyCountryPie from '#lib/CompanyCountryPie.svelte';
	import PaidDataUpsell from '#lib/PaidDataUpsell.svelte';

	import type { PageData } from './$types';

	interface Props {
		data: PageData;
	}

	let { data }: Props = $props();

	let hasCountryStats = $derived(
		data.companiesOverview.country_stats && data.companiesOverview.country_stats.length > 0
	);

	let typeName = $derived(
		page.data.companyTypes?.types?.find((t: any) => t.url_slug === page.params.type)?.name ||
			page.params.type ||
			'Companies'
	);

	// Type-specific SEO overrides — add new types here as needed.
	// Falls back to the original generic pattern for unknown types.
	const typeSeo: Record<string, { title: string; description: string }> = {
		'ad-networks': {
			title: 'Ad Network Companies & Tracking Domains | AppGoblin',
			description:
				'Analyze mobile ad network market share, Android/iOS SDK integration counts, and app-ads.txt records across 400+ tracking domains. Download the free CSV dataset.'
		},
		'ad-attribution': {
			title: 'Top Mobile Attribution & MMP Companies | AppGoblin',
			description:
				'Compare mobile attribution platforms and MMPs. Analyze SDK adoption, network integrations, and iOS/Android market share data.'
		},
		'product-analytics': {
			title: 'Mobile Product Analytics & BI Platforms | AppGoblin',
			description:
				'Discover top mobile product analytics tools. Evaluate SDK counts, category reach, and market share across millions of mobile apps.'
		},
		'development-tools': {
			title: 'Mobile Development Tools & API Directory | AppGoblin',
			description:
				'Browse mobile development tools and APIs. View live SDK footprints, backend services, and adoption trends across app stores.'
		},
		'business-tools': {
			title: 'Mobile Business & Enterprise Software | AppGoblin',
			description:
				'Analyze enterprise software and CRM platforms for mobile apps. Filter by SDK adoption, category distribution, and market reach.'
		},
		mediation: {
			title: 'Top Ad Mediation Platforms & SDKs | AppGoblin',
			description:
				'Compare mobile ad mediation networks. Track SDK penetration, supported ad networks, and market share data for publishers.'
		},
		'app-publishers': {
			title: 'Mobile App Publishers & Developer Portfolios | AppGoblin',
			description:
				'Explore top mobile app publishers. Analyze app portfolios, global store performance, category presence, and SDK stacks.'
		}
	};

	let seo = $derived(typeSeo[page.params.type!]);
	let seoTitle = $derived(seo?.title || `${typeName} Companies & Domains | AppGoblin`);
	let seoDescription = $derived(
		seo?.description ||
			`Explore leading ${typeName} by app coverage, SDK/API footprint, and app-ads.txt visibility in the mobile ecosystem.`
	);
</script>

<svelte:head>
	<title>{seoTitle}</title>
	<meta name="description" content={seoDescription} />
	<meta name="robots" content="index, follow" />
	<link rel="canonical" href={page.url.href} />
</svelte:head>

{#if typeof data.companiesOverview == 'string'}
	Failed to load companies.
{:else if data.companiesOverview.categories}
	<CompaniesTableGrid>
		{#snippet mainTable()}
			{#if data.companiesOverview && data.companiesOverview.companies_overview.length > 0}
				<CompaniesOverviewTable data={data.companiesOverview.companies_overview} />
			{/if}
			<PaidDataUpsell class="mt-4" />
		{/snippet}
		{#snippet countryChart()}
			{#if hasCountryStats}
				<WhiteCard>
					{#snippet title()}
						<span>{typeName} by Country</span>
					{/snippet}
					<CompanyCountryPie plotData={data.companiesOverview.country_stats} />
				</WhiteCard>
			{/if}
		{/snippet}
	</CompaniesTableGrid>
{/if}
