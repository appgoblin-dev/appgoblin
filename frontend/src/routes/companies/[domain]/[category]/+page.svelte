<script lang="ts">
	import type { CompanyCategoryDetails } from '../../../../types';
	import { page } from '$app/state';

	import TotalsBox from '$lib/TotalsBox.svelte';
	import CompaniesLayout from '$lib/CompaniesLayout.svelte';
	import WhiteCard from '$lib/WhiteCard.svelte';
	import CompanyTableGrid from '$lib/CompanyTableGrid.svelte';
	interface Props {
		data: CompanyCategoryDetails;
	}

	let { data }: Props = $props();

	let company_category = $derived(page.params.category!);
	let companyName = $derived(
		data.companyTree.queried_company_name || data.companyTree.queried_company_domain
	);
</script>

<CompaniesLayout>
	{#snippet card1()}
		<WhiteCard>
			{#snippet title()}
				{companyName}'s Totals
			{/snippet}
			{#if data.companyDetails.categories[company_category]}
				<TotalsBox
					companyName={data.companyTree.queried_company_name ||
						data.companyTree.queried_company_domain}
					myTotals={data.companyDetails.categories[company_category]}
					myType={{ name: 'All Companies & Domains', url_slug: 'all-companies' }}
				/>
			{:else}
				<p>
					No apps found for
					<span class="text-primary-900-100 font-bold">{company_category}</span>
					category
				</p>
			{/if}
		</WhiteCard>
	{/snippet}
</CompaniesLayout>

<CompanyTableGrid
	tableData={data.companyCategoryApps}
	detailsData={data.companyDetails}
	category={company_category}
	isSecondaryDomain={data.companyTree.is_secondary_domain}
	{companyName}
/>
