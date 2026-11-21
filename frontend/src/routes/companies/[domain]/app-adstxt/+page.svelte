<script lang="ts">
	import type { CompanyFullDetails } from '../../../../types';
	import AdsTxtPubIDsTable from '#lib/AdsTxtPubIDsTable.svelte';
	import CompanySectionLink from '#lib/utils/CompanySectionLink.svelte';

	interface Props {
		data: CompanyFullDetails;
	}

	let { data }: Props = $props();
</script>

<section class="mb-4 space-y-2">
	<h2 class="text-xl font-semibold">App-ads.txt Publisher IDs</h2>
	<p class="text-sm mb-3">
		App-ads.txt records are mapped to real app IDs and updated daily, so you can audit direct and
		reseller relationships for fraud detection, supply-path analysis, and partner prospecting.
		Explore <CompanySectionLink slug="apps-added-adstxt">recently added</CompanySectionLink> and
		<CompanySectionLink slug="apps-lost-adstxt">recently lost app-ads.txt apps</CompanySectionLink>,
		or see <CompanySectionLink slug="data-exports">client app exports</CompanySectionLink>.
	</p>
</section>

{#if data.companyDetails && data.companyDetails.adstxt_publishers_overview}
	<section class="preset-filled-surface-100-900 p-2 md:p-8 mt-2 md:mt-4">
		<div class="grid md:grid-cols-2 gap-4">
			{#if data.companyDetails.adstxt_publishers_overview.google && data.companyDetails.adstxt_publishers_overview.google.direct}
				<section>
					<h3 class="text-lg font-semibold mb-4">ANDROID DIRECT PUBLISHER IDS</h3>
					<AdsTxtPubIDsTable
						entries_table={data.companyDetails.adstxt_publishers_overview.google.direct}
					/>
				</section>
			{/if}
			{#if data.companyDetails.adstxt_publishers_overview.apple && data.companyDetails.adstxt_publishers_overview.apple.direct}
				<section>
					<h3 class="text-lg font-semibold mb-4">IOS DIRECT PUBLISHER IDS</h3>
					<AdsTxtPubIDsTable
						entries_table={data.companyDetails.adstxt_publishers_overview.apple.direct}
					/>
				</section>
			{/if}
		</div>
		<span class="text-xs md:text-sm text-gray-500">
			Full app-ads.txt data updated daily is available. <a href="/about">See pricing page</a>.
		</span>
	</section>
{:else}
	<p class="text-center p-4">No app-ads.txt data found for this company.</p>
{/if}
