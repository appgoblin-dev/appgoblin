<script lang="ts">
	import { page } from '$app/state';
	import CompaniesOverviewTable from '#lib/CompaniesOverviewTable.svelte';
	import CompaniesTableGrid from '#lib/CompaniesTableGrid.svelte';
	import PaidDataUpsell from '#lib/PaidDataUpsell.svelte';

	let { data } = $props();

	let categoryName = $derived(
		data.appCats?.categories?.find((cat: any) => cat.id === page.params.category)?.name ||
			page.params.category ||
			'All'
	);
</script>

<svelte:head>
	<title>{categoryName} App Companies & Ad Networks | AppGoblin</title>
	<meta
		name="description"
		content="Browse {categoryName} app companies, ad networks, and analytics providers. See SDK usage, API adoption, and app-ads.txt coverage by category."
	/>
	<meta name="robots" content="index, follow" />
	<link rel="canonical" href={page.url.href} />
</svelte:head>

{#if typeof data.companiesOverview == 'string'}
	Failed to load companies.
{:else if data.companiesOverview.categories.categories}
	<CompaniesTableGrid>
		{#snippet mainTable()}
			{#if data.companiesOverview && data.companiesOverview.companies_overview.length > 0}
				<CompaniesOverviewTable
					data={data.companiesOverview.companies_overview}
					showLimitNote={true}
				/>
			{/if}
			<PaidDataUpsell class="mt-4" />
		{/snippet}
	</CompaniesTableGrid>
{:else}
	<p>categegories.all is missing!</p>
{/if}
