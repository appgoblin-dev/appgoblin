<script lang="ts">
	import type { CompanyFullDetails } from '../../../../types';

	import TotalsBox from '$lib/TotalsBox.svelte';
	import CompanyButton from '$lib/CompanyButton.svelte';
	import CompanyCategoryPie from '$lib/CompanyCategoryPie.svelte';
	import AdsTxtTotalsBox from '$lib/AdsTxtTotalsBox.svelte';
	import CompanyTableGrid from '$lib/CompanyTableGrid.svelte';
	import CompanyTree from '$lib/CompanyTree.svelte';
	import WhiteCard from '$lib/WhiteCard.svelte';
	import CompaniesLayout from '../../../../lib/CompaniesLayout.svelte';
	import { countryCodeToEmoji } from '$lib/utils/countryCodeToEmoji';
	interface Props {
		data: CompanyFullDetails;
	}

	let { data }: Props = $props();
</script>

<CompaniesLayout>
	{#snippet card1()}
		{#if !data.companyTree.is_secondary_domain}
			<WhiteCard>
				{#if typeof data.companyParentCategories == 'string'}
					<p class="text-red-500 text-center">Failed to load company details.</p>
				{:else if data.companyParentCategories && data.companyParentCategories.length > 0}
					<WhiteCard>
						{#snippet title()}
							<span>Company Apps</span>
						{/snippet}

						<TotalsBox
							companyName={data.companyTree.queried_company_name ||
								data.companyTree.queried_company_domain}
							myTotals={data.companyDetails.categories.all}
							myType={{ name: 'All Companies & Domains', url_slug: 'all-companies' }}
							hideAdstxtApps={true}
						/>
						{#if data.companyDetails && data.companyDetails.adstxt_ad_domain_overview && data.companyDetails.adstxt_ad_domain_overview.google}
							<AdsTxtTotalsBox myTotals={data.companyDetails.adstxt_ad_domain_overview} />
						{/if}
					</WhiteCard>
				{/if}
			</WhiteCard>
		{/if}
	{/snippet}

	{#snippet card2()}
		{#if !data.companyTree.is_secondary_domain}
			<WhiteCard>
				{#snippet title()}
					<span>Apps by Category</span>
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
				<span>Related Entities</span>
			{/snippet}
			<div class="p-2">
				{#if typeof data.companyTree == 'string'}
					<p class="text-red-500 text-center">Failed to load company tree.</p>
				{:else if data.companyTree && data.companyTree.children_companies.length > 0}
					<!-- HAS CHILD COMPANY -->
					<CompanyTree myTree={data.companyTree} />
				{:else if data.companyTree && data.companyTree.parent_company_domain}
					<!-- HAS PARENT COMPANY -->
					<p class="text-lg font-semibold mb-4">Parent Company:</p>
					<CompanyButton
						companyName={data.companyTree.parent_company_name}
						companyDomain={data.companyTree.parent_company_domain}
						companyLogoUrl={data.companyTree.parent_company_logo_url}
					/>
				{:else if data.companyTree.is_secondary_domain}
					<!-- UNKNOWN COMPANY -->
					<p class="text-red-200 text-center">
						This domain is not associated with any apps or companies yet. If you would like this
						domain mapped to related SDKs and mobile apps please contact us.
					</p>
				{:else}
					<!-- REGULAR COMPANY (no child or parent companies) -->
				{/if}
				{#if data.companyTree && data.companyTree.domains && data.companyTree.domains.length > 1}
					<h2 class="text-lg font-semibold mb-4">Associated Domains</h2>
					<div class="flex flex-col gap-1">
						{#each data.companyTree.domains as domain}
							<div class="">
								<!-- Domain URL -->
								<div
									class="font-semibold text-md"
									title={`IP addresses for this domain commonly resolve to: ${domain.country.join(', ')}`}
								>
									<span
										><a href="/companies/{domain.tld_url}">{domain.tld_url}</a>
										<!-- Countries as flags -->
										{#if domain.country.length > 0}
											<span class="gap-2 ml-2">
												{#each domain.country as country}
													<span class="text-lg">{countryCodeToEmoji(country)}</span>
												{/each}
											</span>
										{/if}
									</span>
								</div>
								<!-- Organizations -->
								{#if domain.org.length > 0}
									<div class="text-sm text-gray-600">
										<span class="text-gray-500">{domain.org.join(', ')}</span>
									</div>
								{/if}
							</div>
						{/each}
					</div>
				{/if}
			</div>
		</WhiteCard>
	{/snippet}
</CompaniesLayout>

{#if typeof data.companyTopApps == 'string'}
	Failed to load company's apps.
{:else}
	<CompanyTableGrid
		tableData={data.companyTopApps}
		detailsData={data.companyDetails}
		category="all"
		isSecondaryDomain={data.companyTree.is_secondary_domain}
	/>
{/if}
