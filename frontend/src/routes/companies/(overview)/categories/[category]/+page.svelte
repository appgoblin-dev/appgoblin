<script lang="ts">
	import CompaniesOverviewTable from '$lib/CompaniesOverviewTable.svelte';
	import CompaniesTableGrid from '$lib/CompaniesTableGrid.svelte';

	let { data } = $props();

	function formatNumber(num: number) {
		return new Intl.NumberFormat('en-US').format(num);
	}
</script>

{#if typeof data.companiesOverview == 'string'}
	Failed to load companies.
{:else if data.companiesOverview.categories.categories}
	<CompaniesTableGrid>
		{#snippet mainTable()}
			{#if data.companiesOverview && data.companiesOverview.companies_overview.length > 0}
				<CompaniesOverviewTable data={data.companiesOverview.companies_overview} />
			{/if}
		{/snippet}

		{#snippet sdkAndroidTotalApps()}
			Android Companies: {formatNumber(
				data.companiesOverview.categories.categories.all.sdk_android_total_companies
			)}
		{/snippet}
		{#snippet sdkIosTotalApps()}
			iOS Companies: {formatNumber(
				data.companiesOverview.categories.categories.all.sdk_ios_total_companies
			)}
		{/snippet}
		{#snippet adstxtAndroidTotalApps()}
			Android Companies:
			{formatNumber(
				data.companiesOverview.categories.categories.all.adstxt_direct_android_total_companies
			)}
		{/snippet}
		{#snippet adstxtIosTotalApps()}
			iOS Companies: {formatNumber(
				data.companiesOverview.categories.categories.all.adstxt_direct_ios_total_companies
			)}
		{/snippet}
	</CompaniesTableGrid>
{:else}
	<p>categegories.all is missing!</p>
{/if}
