<script lang="ts">
	import { page } from '$app/state';
	import CompaniesOverviewTable from '#lib/CompaniesOverviewTable.svelte';
	import CompaniesTableGrid from '#lib/CompaniesTableGrid.svelte';
	import WhiteCard from '#lib/WhiteCard.svelte';
	import CompanyCountryPie from '#lib/CompanyCountryPie.svelte';
	import PaidDataUpsell from '#lib/PaidDataUpsell.svelte';

	let { data } = $props();

	let hasCountryStats = $derived(
		data.companiesOverview.country_stats && data.companiesOverview.country_stats.length > 0
	);

	let typeName = $derived(
		page.data.companyTypes?.types?.find((t: any) => t.url_slug === page.params.type)?.name ||
			page.params.type ||
			''
	);
	let categoryName = $derived(
		data.appCats?.categories?.find((cat: any) => cat.id === page.params.category)?.name ||
			page.params.category ||
			''
	);
</script>

<svelte:head>
	<title>{typeName} Companies in {categoryName} | AppGoblin</title>
	<meta
		name="description"
		content="Browse {typeName} companies operating in the {categoryName} app category. Explore SDK usage, API adoption, and app-ads.txt intelligence."
	/>
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
