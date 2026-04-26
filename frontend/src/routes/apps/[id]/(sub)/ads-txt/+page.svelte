<script lang="ts">
	import AdsTxtTable from '$lib/AdsTxtTable.svelte';
	import type { AdsTxtEntriesResult } from '../../../../../types';
	let { data }: { data: AdsTxtEntriesResult } = $props();
</script>

<div class="p-2 md:p-16 mt-2 md:mt-4">
	{#await data.myAdsTxt}
		Loading App-Ads.txt data...
	{:then adstxt}
		<div class="grid grid-cols-1 md:grid-cols-2 gap-2">
			<div class="mt-2 md:mt-4 md:p-4">
				<h4 class="h4 md:h3 p-2 mt-2">Direct App-Ads.Txt</h4>
				{#if adstxt.direct_entries && adstxt.direct_entries.length > 0}
					<AdsTxtTable data={adstxt.direct_entries} />
				{:else}
					<p class="p-2">No direct App-Ads.txt entries found.</p>
				{/if}
			</div>
			<div class="mt-2 md:mt-4 md:p-4">
				<h4 class="h4 md:h3 p-2 mt-2">Reseller App-Ads.Txt Entries</h4>
				{#if adstxt.reseller_entries && adstxt.reseller_entries.length > 0}
					<AdsTxtTable data={adstxt.reseller_entries} />
				{:else}
					<p class="p-2">No reseller App-Ads.txt entries found.</p>
				{/if}
			</div>
		</div>
	{/await}
</div>
