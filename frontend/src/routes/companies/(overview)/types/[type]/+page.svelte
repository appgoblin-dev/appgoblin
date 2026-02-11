<script lang="ts">
	import CompaniesOverviewTable from '$lib/CompaniesOverviewTable.svelte';
	import CompaniesTableGrid from '$lib/CompaniesTableGrid.svelte';

	import type { PageData } from './$types';
	import { formatNumber } from '$lib/utils/formatNumber';

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
		{#snippet sdkAndroidTotalApps()}
			<span
				>Android Companies:
				{formatNumber(data.companiesOverview.categories.categories.all.sdk_android_total_companies)}
			</span>
		{/snippet}
		{#snippet sdkIosTotalApps()}
			<span
				>iOS Companies: {formatNumber(
					data.companiesOverview.categories.categories.all.sdk_ios_total_companies
				)}</span
			>
		{/snippet}
		{#snippet adstxtAndroidTotalApps()}
			<span
				>Android Companies: {formatNumber(
					data.companiesOverview.categories.categories.all.adstxt_direct_android_total_companies
				)}</span
			>
		{/snippet}
		{#snippet adstxtIosTotalApps()}
			<span
				>iOS Companies: {formatNumber(
					data.companiesOverview.categories.categories.all.adstxt_direct_ios_total_companies
				)}</span
			>
		{/snippet}
	</CompaniesTableGrid>
{/if}
