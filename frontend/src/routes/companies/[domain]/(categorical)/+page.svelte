<script lang="ts">
	import type { CompanyFullDetails } from '../../../../types';
	import { Dialog, Portal } from '@skeletonlabs/skeleton-svelte';

	import SideBarCompanies from '$lib/SideBarCompanies.svelte';

	import TotalsBox from '$lib/TotalsBox.svelte';
	import CompanyCategoryPie from '$lib/CompanyCategoryPie.svelte';
	import AdsTxtTotalsBox from '$lib/AdsTxtTotalsBox.svelte';
	import CompanyTableGrid from '$lib/CompanyTableGrid.svelte';
	import HierarchyTree from '$lib/HierarchyTree.svelte';
	import WhiteCard from '$lib/WhiteCard.svelte';
	import CompaniesLayout from '$lib/CompaniesLayout.svelte';
	interface Props {
		data: CompanyFullDetails;
	}

	let { data }: Props = $props();
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
	let hasHierarchyContext = $derived(
		Boolean(data.companyTree.company_domain || data.companyTree.parent)
	);
	let queriedIsMappedCompany = $derived(
		data.companyTree.queried_domain === data.companyTree.company_domain
	);
	let associatedDomains = $derived(data.companyTree?.domains ?? []);
</script>

<p class="text-sm mb-4">
	AppGoblin intelligence for {companyName} SDKs, API calls, app-ads.txt records. Browse {companyName}
	creatives, and mediation relationships tied to real mobile app IDs so you can evaluate technical footprint
	and competitive position quickly.
</p>

<CompaniesLayout>
	{#snippet card1()}
		{#if !data.companyTree.is_secondary_domain}
			<WhiteCard>
				{#if typeof data.companyParentCategories == 'string'}
					<p class="text-red-500 text-center">Failed to load company details.</p>
				{:else if data.companyParentCategories && data.companyParentCategories.length > 0}
					<WhiteCard>
						{#snippet title()}
							<span>{companyName}'s Company Apps</span>
						{/snippet}

						<TotalsBox
							{companyName}
							myTotals={data.companyDetails.categories.all}
							myType={{ name: 'All Companies & Domains', url_slug: 'all-companies' }}
							hideAdstxtApps={true}
							isSecondaryDomain={data.companyTree.is_secondary_domain}
						/>
						{#if data.companyDetails && data.companyDetails.adstxt_ad_domain_overview && data.companyDetails.adstxt_ad_domain_overview.google}
							<AdsTxtTotalsBox myTotals={data.companyDetails.adstxt_ad_domain_overview} />
						{/if}
					</WhiteCard>
				{/if}
			</WhiteCard>
		{:else if typeof data.companyParentCategories == 'string'}
			<p class="text-red-500 text-center">Failed to load company details.</p>
		{:else if data.companyParentCategories && data.companyParentCategories.length > 0}
			<WhiteCard>
				{#snippet title()}
					<span>{companyName} Apps</span>
				{/snippet}
				<p class="text-sm text-gray-600 mb-2">
					This queried domain maps to {data.companyTree.company_name ||
						data.companyTree.company_domain}.
					{#if hasHigherLevelParent}
						The larger parent company is {data.companyTree.parent?.company_name ||
							data.companyTree.parent?.company_domain}.
					{/if}
				</p>

				<TotalsBox
					{companyName}
					myTotals={data.companyDetails.categories.all}
					myType={{ name: 'All Companies & Domains', url_slug: 'all-companies' }}
					hideAdstxtApps={true}
					isSecondaryDomain={data.companyTree.is_secondary_domain}
				/>
				{#if data.companyDetails && data.companyDetails.adstxt_ad_domain_overview && data.companyDetails.adstxt_ad_domain_overview.google}
					<AdsTxtTotalsBox myTotals={data.companyDetails.adstxt_ad_domain_overview} />
				{/if}
			</WhiteCard>
		{/if}
	{/snippet}

	{#snippet card2()}
		{#if !data.companyTree.is_secondary_domain}
			<WhiteCard>
				{#snippet title()}
					<span>{companyName}'s Apps by Category</span>
				{/snippet}
				<div>
					{#await data.companyParentCategories}
						<span class="text-lg">Loading...</span>
					{:then myPieData}
						{#if typeof myPieData == 'string'}
							<p class="text-red-500 text-center">Failed to load parent categories.</p>
						{:else if myPieData}
							<CompanyCategoryPie plotData={myPieData} />
						{/if}
					{:catch error}
						<p class="text-red-500 text-center">{error.message}</p>
					{/await}
				</div>
			</WhiteCard>
		{/if}
	{/snippet}
	{#snippet card3()}
		<WhiteCard>
			{#snippet title()}
				<span>{companyName}'s Related Entities</span>
			{/snippet}
			<div class="p-2">
				{#if hasHierarchyContext}
					<HierarchyTree
						companyTree={data.companyTree}
						{hasHigherLevelParent}
						{queriedIsMappedCompany}
						{associatedDomains}
						showTruncated={true}
					/>
				{/if}

				{#if typeof data.companyTree == 'string'}
					<p class="text-red-500 text-center">Failed to load company tree.</p>
				{:else if data.companyTree.is_orphan}
					<p class="text-sm text-gray-500 text-center">
						This domain has not been mapped to a company yet. If you would like it added, please <a
							href="/contact"
							class="underline hover:text-gray-700">reach out</a
						>.
					</p>
				{:else}
					<!-- REGULAR COMPANY (no child or parent companies) -->
				{/if}
			</div>
		</WhiteCard>
	{/snippet}
</CompaniesLayout>

{#if typeof data.companyTopApps == 'string'}
	Failed to load company's apps.
{:else}
	<CompanyTableGrid tableData={data.companyTopApps} companyName={companyName || ''} />
{/if}
{#if data.companyTree && (associatedDomains.length > 0 || data.companyTree.children.length > 0)}
	<section class="mt-6">
		<h2 class="text-xl font-semibold mb-2">Full Hierarchy</h2>
		<p class="text-sm text-gray-600 mb-3">
			Complete company ownership structure and all associated domains.
		</p>
		<HierarchyTree
			companyTree={data.companyTree}
			{hasHigherLevelParent}
			{queriedIsMappedCompany}
			{associatedDomains}
			showTruncated={false}
		/>
	</section>
{/if}

<div class="md:hidden sticky bottom-0 bg-surface-50-950 p-2">
	<!-- Small screen version of the side bar -->
	<Dialog>
		<Dialog.Trigger class="btn preset-filled">APP FILTERS</Dialog.Trigger>
		<Portal>
			<Dialog.Positioner class="fixed inset-0 z-50 flex justify-start">
				<Dialog.Content class="h-screen card w-sm p-4 space-y-4 shadow-xl max-w-[320px]">
					<SideBarCompanies myCatData={data.appCats} />
				</Dialog.Content>
			</Dialog.Positioner>
		</Portal>
	</Dialog>
</div>
