<script lang="ts">
	import type { CompanyCategoryDetails } from '../../../../../types';
	import { page } from '$app/state';

	import TotalsBox from '$lib/TotalsBox.svelte';
	import CompaniesLayout from '$lib/CompaniesLayout.svelte';
	import WhiteCard from '$lib/WhiteCard.svelte';
	import CompanyTableGrid from '$lib/CompanyTableGrid.svelte';
	import HierarchyTree from '$lib/HierarchyTree.svelte';
	interface Props {
		data: CompanyCategoryDetails;
	}

	let { data }: Props = $props();

	let company_category = $derived(page.params.category!);
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
	let queriedIsMappedCompany = $derived(
		data.companyTree.queried_domain === data.companyTree.company_domain
	);
	let associatedDomains = $derived(data.companyTree?.domains ?? []);
</script>

<CompaniesLayout>
	{#snippet card1()}
		<WhiteCard>
			{#snippet title()}
				{companyName}'s Totals
			{/snippet}
			{#if data.companyDetails.categories[company_category]}
				<TotalsBox
					{companyName}
					myTotals={data.companyDetails.categories[company_category]}
					myType={{ name: 'All Companies & Domains', url_slug: 'all-companies' }}
					isSecondaryDomain={data.companyTree.is_secondary_domain}
				/>
			{:else}
				<p>
					No apps found for
					<span class=" font-bold">{company_category}</span>
					category
				</p>
			{/if}
		</WhiteCard>
	{/snippet}
	{#snippet card3()}
		{#if data.companyTree.company_domain || data.companyTree.parent}
			<WhiteCard>
				{#snippet title()}
					<span>{companyName}'s Related Entities</span>
				{/snippet}
				<div class="p-2">
					<p class="text-xs font-semibold uppercase tracking-wide mb-2">Hierarchy</p>
					<div class="rounded-md border border-surface-200-800 p-3">
						<HierarchyTree
							companyTree={data.companyTree}
							{hasHigherLevelParent}
							{queriedIsMappedCompany}
							{associatedDomains}
							showTruncated={true}
						/>
					</div>
				</div>
			</WhiteCard>
		{/if}
	{/snippet}
</CompaniesLayout>

<CompanyTableGrid tableData={data.companyCategoryApps} companyName={companyName || ''} />

{#if associatedDomains.length > 0 || data.companyTree.children.length > 0}
	<section class="mt-6">
		<h2 class="text-xl font-semibold mb-2">Full Hierarchy</h2>
		<p class="text-sm text-gray-600 mb-3">
			Complete company ownership structure and all associated domains.
		</p>
		<div class="p-4 rounded-md border border-surface-200-800">
			<HierarchyTree
				companyTree={data.companyTree}
				{hasHigherLevelParent}
				{queriedIsMappedCompany}
				{associatedDomains}
				showTruncated={false}
			/>
		</div>
	</section>
{/if}
