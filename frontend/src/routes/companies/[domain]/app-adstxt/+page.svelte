<script lang="ts">
	import type { CompanyFullDetails } from '../../../../types';
	import AdsTxtPubIDsTable from '$lib/AdsTxtPubIDsTable.svelte';

	interface Props {
		data: CompanyFullDetails;
	}

	let { data }: Props = $props();
</script>

{#if data.companyDetails && data.companyDetails.adstxt_publishers_overview}
	<div class="card preset-tonal p-2 md:p-8 mt-2 md:mt-4">
		<div class="grid md:grid-cols-2 gap-4">
			{#if data.companyDetails.adstxt_publishers_overview.google && data.companyDetails.adstxt_publishers_overview.google.direct}
				<div>
					<h2 class="text-lg font-semibold mb-4">ANDROID DIRECT PUBLISHER IDS</h2>
					<AdsTxtPubIDsTable
						entries_table={data.companyDetails.adstxt_publishers_overview.google.direct}
					/>
				</div>
			{/if}
			{#if data.companyDetails.adstxt_publishers_overview.apple && data.companyDetails.adstxt_publishers_overview.apple.direct}
				<div>
					<h2 class="text-lg font-semibold mb-4">IOS DIRECT PUBLISHER IDS</h2>
					<AdsTxtPubIDsTable
						entries_table={data.companyDetails.adstxt_publishers_overview.apple.direct}
					/>
				</div>
			{/if}
		</div>
		<span class="text-xs md:text-sm text-gray-500">
			Full app-ads.txt data updated daily is available. <a href="/about">See pricing page</a>.
		</span>
	</div>
{:else}
	<p class="text-center p-4">No app-ads.txt data found for this company.</p>
{/if}
