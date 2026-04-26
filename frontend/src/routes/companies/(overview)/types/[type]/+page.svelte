<script lang="ts">
	import CompaniesOverviewTable from '$lib/CompaniesOverviewTable.svelte';
	import CompaniesTableGrid from '$lib/CompaniesTableGrid.svelte';

	import type { PageData } from './$types';

	interface Props {
		data: PageData;
	}

	let { data }: Props = $props();
</script>

{#if typeof data.companiesOverview == 'string'}
	Failed to load companies.
{:else if data.companiesOverview.categories}
	<CompaniesTableGrid>
		{#snippet mainTable()}
			{#if data.companiesOverview && data.companiesOverview.companies_overview.length > 0}
				<CompaniesOverviewTable data={data.companiesOverview.companies_overview} />
			{/if}
		{/snippet}
	</CompaniesTableGrid>
{/if}
